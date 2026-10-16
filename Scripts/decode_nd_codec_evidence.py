#!/usr/bin/env python3
"""Evidence-grade ANIM/ANIM_RAWCHANNELS association and codec stream inventory.

This utility does not pretend to decode Naughty Dog's proprietary bit/interpolation
codec.  It fixes a subtle association error in earlier reports: an ANIM resource's
``+0x40`` page-relative pointer identifies the RAWCHANNELS resource, while the
codec header is a separate block which commonly ends exactly at the ANIM resource
start.  The script records both links, validates the header clocks, and exports the
raw half stream with conservative dimensionality hypotheses.  No bone name or
world-unit interpretation is asserted.
"""
from __future__ import annotations
import csv, hashlib, json, math, struct, sys
from pathlib import Path

MAGIC = 0x41430102
ROOT = 0x509903BB65AC341E

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def u64(b, o): return struct.unpack_from('<Q', b, o)[0]
def f32(b, o): return struct.unpack_from('<f', b, o)[0]
def hs(b): return [float(struct.unpack_from('<e', b, i)[0]) for i in range(0, len(b) - 1, 2)]
def cstr(b, o):
    if o < 0 or o >= len(b): return ''
    e = b.find(b'\0', o)
    return b[o:e if e >= 0 else len(b)].decode('utf-8', 'replace')
def sha256(b): return hashlib.sha256(b).hexdigest()

def parse(path: Path):
    b = path.read_bytes()
    vals = struct.unpack_from('<11I', b, 0)
    page_count, page_table = vals[4], vals[5]
    pages = [struct.unpack_from('<3I', b, page_table + 12*i) for i in range(page_count)]
    all_rows, all_samples, clips = [], [], []
    for pi, (po, psz, pflags) in enumerate(pages):
        ec = u16(b, po + 18)
        starts = []
        for ei in range(ec):
            q = po + 20 + 16*ei
            if q + 16 > len(b): continue
            no, ro = struct.unpack_from('<QI', b, q)
            rs = po + ro
            if rs + 16 > len(b): continue
            starts.append((rs, ei, ro, cstr(b, po + u64(b, rs)), cstr(b, po + u64(b, rs + 8))))
        starts.sort()
        raws = []
        for k, (rs, ei, ro, name, typ) in enumerate(starts):
            end = starts[k+1][0] if k + 1 < len(starts) else po + psz
            if typ == 'ANIM_RAWCHANNELS':
                cnt = u32(b, rs + 48) if rs + 52 <= end else 0
                if 0 < cnt <= 4096 and rs + 72 + 16*cnt <= end:
                    hb, pb = rs + 72, rs + 72 + 8*cnt
                    hashes = [u64(b, hb + 8*i) for i in range(cnt)]
                    ptrs = [u64(b, pb + 8*i) for i in range(cnt)]
                    raws.append(dict(rs=rs, end=end, page=pi, entry=ei, ro=ro, count=cnt,
                                     hashes=hashes, ptrs=ptrs, name=name))
        # Codec headers are page-local blocks; retain only plausibly structured ones.
        hits=[]; q=po
        magic_bytes=struct.pack('<I', MAGIC)
        while True:
            q=b.find(magic_bytes, q, po+psz)
            if q < 0: break
            if q + 64 <= len(b):
                psize=u32(b,q+8); groups=u16(b,q+12); frames=u16(b,q+14)
                period=f32(b,q+36); rate=f32(b,q+40)
                if 0 < psize <= psz and 0 < groups < 4096 and 0 < frames < 100000:
                    hits.append(dict(offset=q, rel=q-po, payload_size=psize, groups=groups,
                                     frames=frames, default_rate=f32(b,q+28), period=period,
                                     rate=rate, alt_period=f32(b,q+44),
                                     header_sha256=sha256(b[q:q+64])))
            q += 4
        for rs, ei, ro, name, typ in starts:
            if typ != 'ANIM' or rs + 72 > len(b): continue
            codec_ptr=u64(b, rs + 56)
            raw_ptr=u64(b, rs + 64)
            raw=next((r for r in raws if r['rs'] <= po + raw_ptr < r['end']), None)
            if raw is None: continue
            # Prefer an exact block-end match; this is how the named ANIM block is
            # laid out in the PC build. Fall back to the closest preceding header.
            direct=next((h for h in hits if h['offset'] == po + codec_ptr), None)
            exact=[h for h in hits if h['offset'] + h['payload_size'] == rs]
            prev=[h for h in hits if h['offset'] < rs]
            hdr=direct or (max(exact, key=lambda x:x['offset']) if exact else (max(prev,key=lambda x:x['offset']) if prev else None))
            clip=dict(page=pi, anim_entry=ei, anim_rel=ro, anim_name=name,
                      anim_abs=rs, raw_entry=raw['entry'], raw_rel=raw['ro'],
                      raw_abs=raw['rs'], raw_count=raw['count'],
                      codec=hdr, codec_pointer_rel=codec_ptr, raw_pointer_rel=raw_ptr)
            clips.append(clip)
            for ci, (hv, pv) in enumerate(zip(raw['hashes'], raw['ptrs'])):
                d=po+pv
                if d + 16 > raw['end']: continue
                fmt=u32(b,d); dp=u64(b,d+8); ds=po+dp
                next_data=min([po+x for x in raw['ptrs'] if po+x > ds] + [raw['end']])
                if ds > next_data: continue
                payload=b[ds:next_data]; vals16=hs(payload)
                family=(fmt >> 16) & 0xff
                if family == 0 and ((fmt >> 24) & 0xff):
                    family=(fmt >> 24) & 0xff
                baseline_n = 12 if (fmt & 0x00ffffff) == 0x00fe0001 else (8 if (fmt & 0x00ffffff) == 0x00ff0001 else 7)
                baseline=vals16[:baseline_n]; stream=vals16[baseline_n:]
                # Candidate frame layouts are storage observations. They are not
                # decoded bone tracks. Keep the exact stream and all near matches.
                frames=(hdr or {}).get('frames')
                hypotheses=[]
                if frames:
                    for dim in range(1, 25):
                        for tail in range(0, min(32, len(stream)+1)):
                            n=len(stream)-tail
                            if n == frames*dim or abs(n-frames*dim) <= 2:
                                hypotheses.append(dict(dimension=dim, tail_half=tail,
                                                       stream_half=n, error=n-frames*dim))
                family_dim = {0xe2: 21, 0xfb: 6, 0x02: 3, 0xf7: 3}.get(family)
                framed_core=[]; trailing=[]
                if frames and family_dim:
                    need=frames*family_dim
                    if len(stream) >= need:
                        framed_core=[stream[i:i+family_dim] for i in range(0, need, family_dim)]
                        trailing=stream[need:]
                row=dict(source=path.name, page=pi, anim_entry=ei, anim_name=name,
                         raw_entry=raw['entry'], raw_count=raw['count'], channel_index=ci,
                         hash=f'0x{hv:016x}', format=f'0x{fmt:08x}', family=f'0x{family:02x}',
                         descriptor_rel=pv, data_rel=dp, payload_bytes=len(payload),
                         half_count=len(vals16), baseline_half=baseline,
                         dynamic_half_count=len(stream), frame_count=frames,
                         dimension_hypotheses=hypotheses,
                         observed_family_dimension=family_dim,
                         framed_core_half_count=sum(len(x) for x in framed_core),
                         trailing_half=trailing,
                         framed_core=framed_core)
                all_rows.append(row)
                if hv == ROOT:
                    for si, v in enumerate(stream):
                        all_samples.append(dict(source=path.name,page=pi,anim_entry=ei,
                            anim_name=name,raw_entry=raw['entry'],format=f'0x{fmt:08x}',
                            sample_index=si,value=v))
    return dict(path=str(path), size=len(b), sha256=sha256(b), pages=pages,
                clips=clips, channels=all_rows, root_samples=all_samples)

def main():
    ap=sys.argv[1:]
    if '--' in ap: ap=ap[ap.index('--')+1:]
    src=Path(ap[0]) if ap else Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
    out=Path(ap[1]) if len(ap)>1 else Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels')
    out.mkdir(parents=True,exist_ok=True)
    doc=parse(src)
    (out/'codec_association_evidence.json').write_text(json.dumps(doc,indent=2),encoding='utf-8')
    fields=['source','page','anim_entry','anim_name','raw_entry','raw_count','channel_index','hash','format','family','descriptor_rel','data_rel','payload_bytes','half_count','baseline_half','dynamic_half_count','frame_count','dimension_hypotheses','observed_family_dimension','framed_core_half_count','trailing_half']
    with (out/'codec_channel_inventory.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in doc['channels']:
            q={k:r.get(k) for k in fields};q['baseline_half']=json.dumps(r['baseline_half'],separators=(',',':'));q['dimension_hypotheses']=json.dumps(r['dimension_hypotheses'],separators=(',',':'));q['trailing_half']=json.dumps(r.get('trailing_half',[]),separators=(',',':'));w.writerow(q)
    with (out/'codec_root_stream_samples.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['source','page','anim_entry','anim_name','raw_entry','format','sample_index','value'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(doc['root_samples'])
    with (out/'codec_framed_core.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['source','page','anim_entry','anim_name','raw_entry','channel_index','hash','format','frame_index','dimension','values','trailing_half'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in doc['channels']:
            core=r.get('framed_core') or []
            for fi,vals in enumerate(core):
                w.writerow({'source':r['source'],'page':r['page'],'anim_entry':r['anim_entry'],'anim_name':r['anim_name'],'raw_entry':r['raw_entry'],'channel_index':r['channel_index'],'hash':r['hash'],'format':r['format'],'frame_index':fi,'dimension':len(vals),'values':json.dumps(vals,separators=(',',':')),'trailing_half':json.dumps(r.get('trailing_half',[]),separators=(',',':'))})
    lines=['# Corrected ANIM codec association evidence','',f'- Source: `{src}`',f'- ANIM clips linked: {len(doc["clips"])}',f'- Channel descriptors: {len(doc["channels"])}',f'- Root hash channels: {len(doc["root_samples"])} samples exported.', '', 'The ANIM +0x40 pointer is resolved into the containing ANIM_RAWCHANNELS resource. Codec headers are selected by exact `header_offset + payload_size == ANIM_resource_start` when available. Header frame clocks are recorded verbatim. Half streams are byte-accurate storage observations; dimensionality hypotheses are listed only when their counts fit the header frame count and are not bone/units claims.', '', '| Clip | Page/ANIM | RAW | Header | Frames | Groups |', '|---|---|---|---|---:|---:|']
    for c in doc['clips'][:200]:
        h=c.get('codec') or {}; lines.append(f"| `{c['anim_name']}` | p{c['page']}/e{c['anim_entry']} | e{c['raw_entry']} ({c['raw_count']} ch) | `{h.get('rel','?')}` | {h.get('frames','?')} | {h.get('groups','?')} |" )
    (out/'CODEC_ASSOCIATION_EVIDENCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'clips':len(doc['clips']),'channels':len(doc['channels']),'root_samples':len(doc['root_samples']),'json':str(out/'codec_association_evidence.json')},indent=2))
if __name__=='__main__': main()
