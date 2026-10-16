#!/usr/bin/env python3
import csv, json, math, os, struct
from pathlib import Path
ROOT_HASH=0x509903bb65ac341e

def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def u64(b,o):return struct.unpack_from('<Q',b,o)[0]
def cstr(b,o):
 e=b.find(b'\0',o)
 return b[o:e].decode('utf8','replace') if e>=0 else ''
def halfs(x):return [float(struct.unpack_from('<e',x,i)[0]) for i in range(0,len(x)-1,2)]
def parse(path):
 b=Path(path).read_bytes(); magic,hdr,li,lo,np,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(np)]; allrows=[]
 for pi,(po,ps,pflags) in enumerate(pages):
  ec=u16(b,po+18); starts=[]
  for ei in range(ec):
   no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro
   if rs+16>len(b):continue
   name=cstr(b,po+u64(b,rs));typ=cstr(b,po+u64(b,rs+8)); starts.append((rs,ei,ro,name,typ))
  raw=[]
  for rs,ei,ro,name,typ in starts:
   if typ!='ANIM_RAWCHANNELS':continue
   end=min([x[0] for x in starts if x[0]>rs]+[po+ps]); count=u32(b,rs+48)
   if count>4096 or rs+72+16*count>end:continue
   hs=[u64(b,rs+72+8*i) for i in range(count)]; ptrs=[u64(b,rs+72+8*count+8*i) for i in range(count)]
   if ROOT_HASH not in hs:continue
   j=hs.index(ROOT_HASH); d=po+ptrs[j]
   if d+16>end:continue
   fmt=u32(b,d);dp=u64(b,d+8);ds=po+dp; nd=min([po+x for x in ptrs if po+x>d]+[end]); payload=b[ds:nd] if ds<=nd else b''; hv=halfs(payload); base=hv[:8]; dyn=hv[8:] if len(hv)>8 else []
   # infer storage shape only for known observed families
   # Format words are 0x00CC00TT; the codec family byte is bits 16..23.
   dim=2 if ((fmt>>16)&0xff)==0xfb and dyn and len(dyn)%2==0 else (1 if dyn else 0)
   raw.append({'rs':rs,'end':end,'entry':ei,'name':name,'count':count,'fmt':fmt,'payload':payload,'base':base,'dyn':dyn,'dim':dim,'page':pi,'po':po,'root_index':j})
  def raw_for(t):return next((r for r in raw if r['rs']<=t<r['end']),None)
  for rs,ei,ro,name,typ in starts:
   if typ!='ANIM' or rs+72>len(b):continue
   p1=u64(b,rs+56);p2=u64(b,rs+64); r=raw_for(po+p2)
   if not r:continue
   ct=po+p1; cm=u32(b,ct) if ct+4<=len(b) else 0
   codec={'magic':f'0x{cm:08x}'}
   if cm==0x41430102 and ct+52<=len(b):
    # Codec header clocks: +0x1c is the default 30-Hz presentation rate,
    # +0x24 is the actual sample period, and +0x28 is the actual sample
    # rate.  The previous reader mislabeled +0x1c as sample_rate and +0x28
    # as duration.
    frames=u16(b,ct+14); period=struct.unpack_from('<f',b,ct+36)[0]; rate=struct.unpack_from('<f',b,ct+40)[0]
    codec.update(size=u32(b,ct+8),groups=u16(b,ct+12),frames=frames,
                 default_rate=struct.unpack_from('<f',b,ct+28)[0],
                 sample_rate=rate,sample_period=period,
                 duration=((frames-1)*period if frames>0 and math.isfinite(period) else None),
                 section_offset=u32(b,ct+48))
   frame_hint=codec.get('frames')
   pair_aligned=bool(cm==0x41430102 and r['dim']==2 and frame_hint and len(r['dyn'])<=2000 and abs(len(r['dyn'])-2*frame_hint)<=2)
   pair_samples=[r['dyn'][k:k+2] for k in range(0,len(r['dyn'])-1,2)] if pair_aligned else []
   allrows.append({'source':Path(path).name,'page':pi,'anim_entry':ei,'anim_resource_offset':rs,'anim_name':name,'raw_entry':r['entry'],'raw_resource_offset':r['rs'],'raw_channel_count':r['count'],'root_channel_index':r['root_index'],'root_format':f'0x{r["fmt"]:08x}','root_payload_bytes':len(r['payload']),'root_baseline':json.dumps(r['base'],separators=(',',':')),'root_dynamic_half_count':len(r['dyn']),'root_observed_dimension':r['dim'],'root_pair_frame_alignment':'within_2_half_values' if pair_aligned else 'opaque_or_unaligned','root_dynamic_samples':pair_samples,'codec':codec})
 return allrows

def hsafe(r):return 0

def main():
 out=Path('Exports/AnimationSources/DecodedRawChannels');out.mkdir(parents=True,exist_ok=True)
 paths=[r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak',r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak',r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-pat-hoodie.pak']
 rows=[]
 for p in paths:
  if Path(p).exists(): rows.extend(parse(p))
 trajectories=[dict(r) for r in rows if r.get('root_dynamic_samples')]
 fields=['source','page','anim_entry','anim_resource_offset','anim_name','raw_entry','raw_resource_offset','raw_channel_count','root_channel_index','root_format','root_payload_bytes','root_baseline','root_dynamic_half_count','root_observed_dimension','root_pair_frame_alignment','codec_magic','codec_size','codec_groups','codec_frames','codec_default_rate','codec_sample_rate','codec_sample_period','codec_duration','codec_section_offset']
 verified=sum(1 for r in rows if r['codec'].get('magic')=='0x41430102')
 csvp=out/'named_root_channel_catalog.csv'
 with csvp.open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:
   c=r.pop('codec'); r.pop('root_dynamic_samples',None); q=dict(r,codec_magic=c.get('magic'),codec_size=c.get('size'),codec_groups=c.get('groups'),codec_frames=c.get('frames'),codec_default_rate=c.get('default_rate'),codec_sample_rate=c.get('sample_rate'),codec_sample_period=c.get('sample_period'),codec_duration=c.get('duration'),codec_section_offset=c.get('section_offset'));w.writerow(q)
 summary={'tool':'extract_named_root_catalog.py','root_hash':f'0x{ROOT_HASH:016x}','rows':len(rows),'with_verified_codec_header':verified,'direct_pair_trajectory_clips':len(trajectories),'direct_pair_trajectory_samples':sum(len(r.get('root_dynamic_samples',[])) for r in trajectories),'sources':sorted(set(r['source'] for r in rows)),'status':'ANIM names are linked to raw resource pointers; root hash is a raw-channel identity, not a bone mapping; codec interpolation remains unresolved'}
 (out/'named_root_channel_catalog.json').write_text(json.dumps(summary,indent=2));
 trajp=out/'named_root_trajectory_samples.csv'
 with trajp.open('w',newline='',encoding='utf8') as f:
  fields2=['source','page','anim_entry','anim_name','root_format','codec_magic','codec_frames','codec_sample_rate','root_dynamic_half_count','sample_index','value0','value1']
  w=csv.DictWriter(f,fieldnames=fields2);w.writeheader()
  for r in trajectories:
   c=r['codec']
   for i,s in enumerate(r.get('root_dynamic_samples',[])):
    w.writerow({'source':r['source'],'page':r['page'],'anim_entry':r['anim_entry'],'anim_name':r['anim_name'],'root_format':r['root_format'],'codec_magic':c.get('magic'),'codec_frames':c.get('frames'),'codec_sample_rate':c.get('sample_rate'),'root_dynamic_half_count':r['root_dynamic_half_count'],'sample_index':i,'value0':s[0],'value1':s[1]})
 (out/'named_root_trajectory_samples.json').write_text(json.dumps(trajectories,indent=2),encoding='utf8')
 (out/'NAMED_ROOT_CHANNEL_CATALOG.md').write_text('# Named root-channel catalog\n\nThe catalog links real ANIM resource labels to the ANIM_RAWCHANNELS resource reached by the package pointer. It records the root-candidate channel format, raw payload size, baseline half values, and codec header frame clocks when the `0x41430102` header is present. The channel hash is retained as an opaque identity; no bone name, units, or proprietary interpolation are inferred.\n\n'+json.dumps(summary,indent=2)+'\n',encoding='utf8')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
