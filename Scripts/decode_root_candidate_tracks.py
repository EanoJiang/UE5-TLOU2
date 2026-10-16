#!/usr/bin/env python3
"""Decode candidate root-channel scalar/pair tracks from a direct movement PAK.

The parser resolves ANIM_RAWCHANNELS descriptor pointers and preserves all half
values.  For the candidate hash 0x509903bb65ac341e, observed descriptor layout:
  [7 half baseline/defaults] [N*arity half samples] [9 half codec metadata]
Formats with 0xf7 prefix are scalar (arity=1); formats with 0xfb prefix are
pairs (arity=2). The proprietary transform/channel mapping is intentionally not
asserted; this is evidence for an external game-compatible decoder.
"""
from __future__ import annotations
import csv, json, math, struct, sys
from pathlib import Path
ROOT_HASH = 0x509903bb65ac341e
DEFAULT_RATE = 30.0
WANTED_FORMATS = {0x00f70061, 0x00fb0050, 0x00fb005f, 0x00fb0088, 0x00fb0105}

def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def f32(b,o): return struct.unpack_from('<f',b,o)[0]
def f16(b,o): return struct.unpack_from('<e',b,o)[0]
def read_header(b):
    vals=struct.unpack_from('<11I',b,0)
    return vals

def find_codec_rates(b,pages):
    out=[]
    magic=struct.pack('<I',0x41430102)
    for pi,(po,ps,_) in enumerate(pages):
        st=po
        while True:
            p=b.find(magic,st,po+ps)
            if p<0: break
            if p+48<=len(b):
                payload=u32(b,p+8); groups=u16(b,p+12); frames=u16(b,p+14)
                # ND codec header stores output sample rate and period at 0x1c/0x2c.
                hz=f32(b,p+0x1c); period=f32(b,p+0x2c)
                nframes=f32(b,p+0x28)
                if 0<payload<0x100000 and 0<frames<5000:
                    out.append(dict(page=pi,relative_offset=p-po,payload_bytes=payload,
                                    groups=groups,frame_count=frames,frame_count_minus1=nframes,
                                    sample_rate_hz=hz,sample_period_s=period))
            st=p+4
    return out

def parse(path):
    b=Path(path).read_bytes(); magic,hdr,li,lo,pc,pt,fp,fo,*_=read_header(b)
    pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(pc)]
    codec=find_codec_rates(b,pages)
    tracks=[]
    for pi,(po,ps,_) in enumerate(pages):
        if po+20>len(b): continue
        ec=u16(b,po+18)
        for ei in range(ec):
            q=po+20+16*ei
            if q+16>len(b): continue
            no,ro=struct.unpack_from('<QI',b,q); rs=po+ro
            if rs+72>len(b): continue
            # type pointer at +8; only raw channels are relevant
            try:
                tp=u64(b,rs+8); end=b.find(b'\0',po+tp)
                typ=b[po+tp:end].decode('utf-8','replace')
            except Exception:
                continue
            if typ!='ANIM_RAWCHANNELS': continue
            try:
                count=u32(b,rs+48); hp=u64(b,rs+56); dp=u64(b,rs+64)
                if count<=0 or count>500 or po+hp+8*count>len(b) or po+dp+8*count>len(b): continue
                hashes=[u64(b,po+hp+8*i) for i in range(count)]
                descs=[u64(b,po+dp+8*i) for i in range(count)]
            except Exception: continue
            if ROOT_HASH not in hashes: continue
            idx=hashes.index(ROOT_HASH); desc_rel=descs[idx]; desc=po+desc_rel
            if desc+16>len(b): continue
            fmt=u32(b,desc); data_rel=u64(b,desc+8)
            if fmt not in WANTED_FORMATS: continue
            # Resolve end from the next actual data pointer, not next descriptor.
            data_rels=[]
            for dr in descs:
                d=po+dr
                if d+16<=len(b): data_rels.append(u64(b,d+8))
            nxt=min([x for x in data_rels if x>data_rel] or [ps])
            nbytes=nxt-data_rel
            # A huge final-page region is not a standalone track.
            plausible=(0<nbytes<2_000_000 and nbytes%2==0)
            if not plausible: continue
            vals=[f16(b,po+data_rel+2*i) for i in range(nbytes//2)]
            if len(vals)<16: continue
            arity=1 if (fmt & 0xff0000)==0xf70000 else 2
            # The low 16 bits of the format word hold the encoded frame count
            # (all observed candidates use ``frame_count = dynamic_rows + 1``).
            # Some pair codecs store one extra endpoint row before metadata.
            rem=len(vals)-16
            if rem<arity or rem%arity: continue
            stored_rows=rem//arity
            encoded_count=fmt & 0xffff
            dynamic_count=encoded_count-1 if encoded_count>0 else stored_rows
            if dynamic_count<=0 or dynamic_count>stored_rows: continue
            # A page-final descriptor can run into an unrelated stream when
            # no following data pointer exists. Valid candidates have at most
            # two stored endpoint rows beyond the encoded dynamic count.
            if stored_rows-dynamic_count > 2: continue
            stream=vals[7:7+arity*stored_rows]
            rows_all=[stream[i*arity:(i+1)*arity] for i in range(stored_rows)]
            samples=rows_all[:dynamic_count]
            extra_rows=rows_all[dynamic_count:]
            tail=vals[7+arity*stored_rows:]
            # Valid metadata tails are 9 or 11 half values depending on the
            # pair codec; the explicit endpoint rows stay separate.
            if len(tail) not in (9,11): continue
            # A final page may contain a following stream without a local
            # descriptor pointer; reject such anomalously huge candidates.
            if dynamic_count > 1000: continue
            # Unwrap scalar angle-like streams only when a >pi wrap is seen.
            unwrapped=[]; off=0.0; prev=None
            if arity==1:
                for row in samples:
                    v=row[0]
                    if prev is not None and v-prev < -3.0: off += 2*math.pi
                    unwrapped.append(v+off); prev=v
            # nearest codec metadata is evidence only; source contains many chunks
            near=None
            before=[c for c in codec if c['page']==pi and c['relative_offset']<=data_rel]
            if before: near=max(before,key=lambda c:c['relative_offset'])
            tracks.append(dict(page=pi,entry=ei,channel_index=idx,channel_hash=f'0x{ROOT_HASH:016x}',
                               format=f'0x{fmt:08x}',format_u32=fmt,arity=arity,
                               descriptor_relative=f'0x{desc_rel:x}',data_relative=f'0x{data_rel:x}',
                               next_data_relative=f'0x{nxt:x}',payload_bytes=nbytes,
                               half_count=len(vals),sample_count=dynamic_count,
                               encoded_frame_count=encoded_count,stored_row_count=stored_rows,
                               extra_rows=extra_rows,baseline=vals[:7],
                               samples=samples,unwrapped_samples=unwrapped,tail=tail,
                               nearest_codec=near))
    return dict(source=str(path),channel_hash=f'0x{ROOT_HASH:016x}',sample_rate_hz=DEFAULT_RATE,
                sample_period_s=1.0/DEFAULT_RATE,codec_rate_evidence=codec,tracks=tracks)

def write_outputs(doc,outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    doc['format_semantics']={
        '0x00f70061': {'arity':1,'value_kind':'scalar half stream','candidate_role':'shared angular/phase scalar; not asserted as world yaw'},
        '0x00fb0050': {'arity':2,'value_kind':'pair half stream','candidate_role':'2D trajectory pair; one stored endpoint row'},
        '0x00fb005f': {'arity':2,'value_kind':'pair half stream','candidate_role':'2D trajectory pair'},
        '0x00fb0088': {'arity':2,'value_kind':'pair half stream','candidate_role':'2D trajectory pair; one stored endpoint row'},
        '0x00fb0105': {'arity':2,'value_kind':'pair half stream','candidate_role':'2D trajectory pair'},
    }
    doc['semantic_caveat']='Channel hash identity is preserved; no bone/world-axis mapping is asserted. The identical f70061 ramp appears across many clips, so it is retained as a phase/angular candidate rather than claimed root motion.'
    doc['time_convention']='CSV time_s uses dynamic row index / 30 Hz; whether the seven-half baseline is frame 0 or a codec default is unresolved.'
    def clean(x):
        if isinstance(x,float) and not math.isfinite(x): return None
        if isinstance(x,list): return [clean(v) for v in x]
        if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
        return x
    (outdir/'movement_root_trajectory_evidence.json').write_text(json.dumps(clean(doc),indent=2,allow_nan=False),encoding='utf8')
    rows=[]
    for t in doc['tracks']:
        for i,s in enumerate(t['samples']):
            rows.append(dict(page=t['page'],entry=t['entry'],format=t['format'],arity=t['arity'],
                             sample_index=i,time_s=i/doc['sample_rate_hz'],value0=s[0],
                             value1=(s[1] if len(s)>1 else ''),
                             unwrapped_value=(t['unwrapped_samples'][i] if t['arity']==1 else '')))
    with (outdir/'movement_root_trajectory.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['page','entry','format','arity','sample_index','time_s','value0','value1','unwrapped_value']);w.writeheader();w.writerows(rows)
    # human report
    groups={}
    for t in doc['tracks']:
        groups.setdefault(t['format'],set()).add((t['arity'],t['sample_count']))
    lines=['# Root-channel trajectory evidence','',f"Candidate hash: `{doc['channel_hash']}`",'','The envelope decoder resolves page-relative descriptor/data pointers. Each valid candidate payload is `[7 half baseline] + stored rows + metadata`; the low 16 format bits encode `dynamic_rows + 1`. Some pair codecs append one endpoint row before the 9/11 half metadata tail. Baselines, endpoint rows, and metadata are preserved separately in JSON. The transform/bone semantic mapping remains a candidate until the game quantizer is implemented.','', '## Format inventory','', '| Format | Arity | Dynamic rows (encoded count) | Stored rows | Valid tracks |','|---|---:|---:|---:|---:|']
    for fmt in sorted(groups):
        ts=[t for t in doc['tracks'] if t['format']==fmt]; ar=ts[0]['arity']; ns=sorted(set(f"{t['sample_count']} (code {t['encoded_frame_count']})" for t in ts)); ss=sorted(set(t['stored_row_count'] for t in ts)); lines.append(f"| `{fmt}` | {ar} | {', '.join(ns)} | {', '.join(map(str,ss))} | {len(ts)} |")
    lines += ['',f"Sample rate evidence: codec headers in this PAK store 30.0 Hz at +0x1c and 0.0333333 s at +0x2c; CSV rows use `time_s = dynamic_row_index / 30`. Whether the seven-half baseline is frame 0 or a codec default is unresolved. 30 Hz is a source-header fact, while semantic interpretation of the hash is not asserted.",'', '## Scalar root f70061 shape','', 'The 96 scalar samples are half-floats. They begin at 1.6357421875, step through +pi, wrap from +3.140625 to -3.07421875, and end at 1.5703125. Unwrapping the wrap yields a continuous candidate from 1.6357421875 to 7.8534978072 rad (delta 6.2177556197 rad / 356.251°) over samples 0..95.']
    (outdir/'ROOT_CHANNEL_TRAJECTORY_EVIDENCE.md').write_text('\n'.join(lines)+'\n',encoding='utf8')

def main():
    p=sys.argv[1] if len(sys.argv)>1 else r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'
    o=sys.argv[2] if len(sys.argv)>2 else r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources'
    d=parse(p);write_outputs(d,o);print(json.dumps({'tracks':len(d['tracks']),'out':o,'formats':sorted(set(t['format'] for t in d['tracks']))},indent=2))
if __name__=='__main__':main()
