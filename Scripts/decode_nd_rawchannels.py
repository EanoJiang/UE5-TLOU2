#!/usr/bin/env python3
"""Decode the self-describing ANIM_RAWCHANNELS layer without claiming a bone map.

This reader is deliberately conservative.  It resolves page-relative pointer fixups,
indexes channel hashes/descriptors and decodes the *documented* half-float baseline
stored by the ND raw-channel records.  For the root-motion candidate hash
0x509903bb65ac341e it additionally exports the post-baseline half stream as a
trajectory candidate.  The channel-to-bone mapping and proprietary codec interpolation
are not guessed.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, struct, sys
from pathlib import Path

ROOT_HASH = 0x509903bb65ac341e
TRANSFORM_HASHES = {
    0xb0599017cc83e626,
    0x16ae0a786c0a62e0,
    0xf2099db117ba20bc,
    0x5a52202ce3f64436,
    ROOT_HASH,
}

def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def f16s(blob):
    vals=[]
    for o in range(0,len(blob)-1,2):
        try: vals.append(float(struct.unpack_from('<e',blob,o)[0]))
        except Exception: vals.append(float('nan'))
    return vals
def finite_stats(vals):
    vv=[x for x in vals if math.isfinite(x)]
    if not vv: return {'count':0,'finite':0}
    return {'count':len(vals),'finite':len(vv),'min':min(vv),'max':max(vv),
            'mean':sum(vv)/len(vv),'zero_fraction':sum(x==0.0 for x in vv)/len(vv)}
def cstr(b,o):
    if o<0 or o>=len(b): return ''
    e=b.find(b'\0',o)
    if e<0: return ''
    return b[o:e].decode('utf-8','replace')
def sha(b): return hashlib.sha256(b).hexdigest()

def parse_pak(path:Path):
    b=path.read_bytes()
    if len(b)<64: raise ValueError('short PAK')
    magic,hdr,login_i,login_o,page_count,page_table,fix_count,fix_off,*_=struct.unpack_from('<11I',b,0)
    if page_count<=0 or page_count>4096: raise ValueError('bad page count')
    pages=[struct.unpack_from('<3I',b,page_table+12*i) for i in range(page_count)]
    records=[]
    for pi,(po,ps,pflags) in enumerate(pages):
        if po+20>len(b): continue
        ec=u16(b,po+18)
        starts=[]
        for ei in range(ec):
            q=po+20+16*ei
            if q+16>len(b): break
            name_off,ro=struct.unpack_from('<QI',b,q); rs=po+ro
            if rs+16>len(b): continue
            # resource header uses page-relative string pointers
            typ=cstr(b,po+u64(b,rs+8))
            name=cstr(b,po+u64(b,rs))
            starts.append((rs,ei,ro,name,typ))
        for idx,(rs,ei,ro,name,typ) in enumerate(starts):
            if typ!='ANIM_RAWCHANNELS': continue
            nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps])
            size=max(0,nxt-rs)
            if rs+72>len(b): continue
            count=u32(b,rs+48)
            # protect malformed pages while retaining evidence
            if count>4096: continue
            hash_base=rs+72
            ptr_base=hash_base+8*count
            if ptr_base+8*count>nxt: continue
            hashes=[u64(b,hash_base+8*i) for i in range(count)]
            ptrs=[u64(b,ptr_base+8*i) for i in range(count)]
            chans=[]
            for ci,(hv,pv) in enumerate(zip(hashes,ptrs)):
                d=po+pv
                if d<rs or d+16>nxt or d>=len(b):
                    chans.append({'index':ci,'hash':f'0x{hv:016x}','descriptor_ptr':int(pv),'error':'descriptor outside resource'})
                    continue
                fmt=u32(b,d)
                data_rel=u64(b,d+8)
                ds=po+data_rel
                # descriptor starts are page-relative and sorted in the page
                # Descriptor pointers delimit the descriptor table, while the
                # payload itself ends at the next *data pointer*.  For the
                # root candidate this distinction is material: the old bound
                # truncated valid tracks by 16 bytes.
                data_ptrs=[]
                for qptr in ptrs:
                    qd=po+qptr
                    if qd+16 <= len(b):
                        try: data_ptrs.append(u64(b,qd+8))
                        except Exception: pass
                if hv == ROOT_HASH:
                    nd=min([po+x for x in data_ptrs if x>data_rel]+[nxt])
                else:
                    nd=min([po+x for x in ptrs if po+x>d]+[nxt])
                if ds<0 or ds>=len(b) or ds>nd:
                    chans.append({'index':ci,'hash':f'0x{hv:016x}','format':f'0x{fmt:08x}','descriptor_ptr':int(pv),'data_ptr':int(data_rel),'error':'payload outside descriptor span'})
                    continue
                payload=b[ds:nd]
                hs=f16s(payload)
                # The static transform codec stores all twelve half values in
                # one payload (quat4, translation3, scale3, two pad values).
                # Do not mislabel the final padding halfs as a trajectory.
                static_transform = (fmt & 0x00ffffff) == 0x00fe0001 and len(hs) <= 12
                static_scalar = (fmt & 0x00ffffff) == 0x00ff0001 and len(hs) <= 8
                tail=[]
                if static_transform or static_scalar:
                    base=hs
                    dyn=[]
                else:
                    root_codec=((fmt>>16)&0xff) in (0xf7,0xfb) and hv==ROOT_HASH
                    if root_codec and len(hs)>=16:
                        base=hs[:7]
                        dyn=hs[7:-9]
                        tail=hs[-9:]
                    else:
                        base=hs[:8] if len(hs)>=8 else hs
                        dyn=hs[8:] if len(hs)>8 else []
                isroot=(hv==ROOT_HASH)
                # Known root streams: 0xfb codecs carry paired payload values;
                # 0xf7 scalar stream carries one value per sample. Keep this as
                # a storage observation, not a semantic transform claim.
                if isroot and dyn:
                    # Format words are stored as 0x00CC00TT: the codec family
                    # byte is bits 16..23 (0xf7/fb/fe/ff), while bits 0..15
                    # carry the track subtype.  Reading bits 24..31 silently
                    # turns every fb paired stream into a scalar stream.
                    hi=(fmt>>16)&0xff
                    dim=2 if hi==0xfb and len(dyn)%2==0 else 1
                else: dim=0
                cr={'index':ci,'hash':f'0x{hv:016x}','format':f'0x{fmt:08x}',
                    'descriptor_ptr':int(pv),'data_ptr':int(data_rel),
                    'payload_offset':int(ds),'payload_bytes':len(payload),
                    'half_count':len(hs),'baseline_half':base,
                    'dynamic_half_count':len(dyn),'dynamic_dimension_observed':dim,
                    'half_stats':finite_stats(hs),'dynamic_stats':finite_stats(dyn),
                    'root_candidate':isroot}
                if tail:
                    cr['metadata_tail_half']=tail
                if static_transform and len(hs)>=4:
                    cr['baseline_quaternion_norm']=math.sqrt(sum(x*x for x in hs[:4]))
                    cr['baseline_transform_fields']={'quaternion':hs[:4],
                                                       'translation':hs[4:7],
                                                       'scale':hs[7:10] if len(hs)>=10 else []}
                if isroot and dyn:
                    if dim==2:
                        cr['dynamic_samples']=[list(dyn[i:i+2]) for i in range(0,len(dyn)-1,2)]
                    else:
                        cr['dynamic_samples']=dyn
                chans.append(cr)
            records.append({'source':path.name,'path':str(path),'sha256':sha(b),
                            'page':pi,'page_offset':po,'page_size':ps,'entry':ei,
                            'resource_offset':rs,'resource_relative_offset':ro,
                            'resource_size':size,'resource_name':name,'resource_type':typ,
                            'channel_count':count,'channels':chans})
    return {'path':str(path),'name':path.name,'size':len(b),'sha256':sha(b),'records':records}

def main():
    # Blender leaves its own flags in sys.argv.  Consume only arguments after
    # the conventional `--` separator so the output never lands in a folder
    # named `--background`.
    argv=sys.argv[1:]
    if '--' in argv: argv=argv[argv.index('--')+1:]
    out=Path(argv[0] if argv else 'Exports/AnimationSources/DecodedRawChannels'); out.mkdir(parents=True,exist_ok=True)
    inputs=argv[1:] if len(argv)>1 else [
      r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak',
      r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak',
      r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-pat-hoodie.pak']
    docs=[]
    for x in inputs:
        p=Path(x)
        if not p.exists(): continue
        try: docs.append(parse_pak(p))
        except Exception as e: docs.append({'path':str(p),'name':p.name,'error':repr(e)})
    allrec=[r for d in docs for r in d.get('records',[])]
    allchan=[(r,c) for r in allrec for c in r.get('channels',[]) if 'error' not in c]
    roots=[(r,c) for r,c in allchan if c.get('root_candidate')]
    manifest={'tool':'decode_nd_rawchannels.py','version':1,
              'scope':'ANIM_RAWCHANNELS structural + half-float baseline/stream only',
              'root_candidate_hash':f'0x{ROOT_HASH:016x}',
              'sources':docs,'resource_count':len(allrec),'channel_count':len(allchan),
              'root_channel_count':len(roots),
              'status':'raw channel payloads decoded; proprietary interpolation and bone mapping intentionally unresolved'}
    (out/'rawchannels_decode_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Compact bind/static transform evidence for reviewers and downstream
    # Blender tooling.  This is a real payload decode, not a proxy pose.
    static_rows=[]
    for r,c in allchan:
        tf=c.get('baseline_transform_fields')
        if not tf: continue
        static_rows.append({'source':r['source'],'page':r['page'],'entry':r['entry'],
            'resource_offset':r['resource_offset'],'channel_index':c['index'],
            'hash':c['hash'],'format':c.get('format'),'payload_bytes':c.get('payload_bytes'),
            'quaternion_norm':c.get('baseline_quaternion_norm'),'transform':tf})
    (out/'static_transform_candidates.json').write_text(json.dumps(static_rows,indent=2),encoding='utf-8')
    # Flat root channel stream export
    csvp=out/'root_channel_tracks.csv'
    fields=['source','page','entry','resource_offset','resource_size','channel_index','hash','format','payload_bytes','baseline_half','sample_index','value0','value1','dynamic_dimension_observed']
    with csvp.open('w',newline='',encoding='utf-8') as f:
      w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
      for r,c in roots:
        dyn=c.get('dynamic_samples',[])
        if not dyn: dyn=[c.get('baseline_half',[])[:1]]
        for si,samp in enumerate(dyn):
          vals=list(samp) if isinstance(samp,list) else [samp]
          w.writerow({'source':r['source'],'page':r['page'],'entry':r['entry'],'resource_offset':r['resource_offset'],'resource_size':r['resource_size'],'channel_index':c['index'],'hash':c['hash'],'format':c.get('format'),'payload_bytes':c.get('payload_bytes'),'baseline_half':json.dumps(c.get('baseline_half',[]),separators=(',',':')),'sample_index':si,'value0':vals[0] if vals else '','value1':vals[1] if len(vals)>1 else '','dynamic_dimension_observed':c.get('dynamic_dimension_observed',0)})
    # Human report
    lines=['# Raw channel decoder evidence','',
      'The reader resolves page-relative pointers and decodes the ANIM_RAWCHANNELS record envelope. Each descriptor is recorded as `(format, data pointer, payload bytes)`; IEEE-754 half values are exposed without applying the proprietary ND interpolation/quantizer.', '',
      f'- Sources: {len(docs)}; resources: {len(allrec)}; channels: {len(allchan)}; root-candidate channels: {len(roots)}.',
      f'- Root candidate hash: `0x{ROOT_HASH:016x}` (hash identity is preserved; no bone name is asserted).',
      '- For static `0xfe0001` descriptors, the first 12 half values validate as quaternion(4), translation(3), scale(3), and two padding values; quaternion norm checks are recorded in JSON.',
      '- For corrected root candidates, the payload layout is seven baseline half values, N raw scalar/pair samples (`0xf7`/`0xfb`), and nine trailing metadata half values. This is a trajectory candidate and requires a game-compatible decoder to assign units/interpolation.', '',
      '## Root candidate examples', '', '| Source | Format | Payload bytes | Dynamic half values | Baseline |', '|---|---|---:|---:|---|']
    for r,c in roots[:80]:
      lines.append(f"| `{r['source']}` p{r['page']} e{r['entry']} | `{c.get('format')}` | {c.get('payload_bytes')} | {c.get('dynamic_half_count')} | `{c.get('baseline_half')}` |")
    lines += ['', 'The companion `root_channel_tracks.csv` is suitable for Blender/UE inspection. It is not labeled as a completed root-motion transform until the proprietary codec and bone/channel map are recovered.']
    (out/'ROOT_CHANNEL_DECODE_EVIDENCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'manifest':str(out/'rawchannels_decode_manifest.json'),'resources':len(allrec),'channels':len(allchan),'root_channels':len(roots),'static_transform_candidates':len(static_rows),'csv':str(csvp)},indent=2))
if __name__=='__main__': main()
