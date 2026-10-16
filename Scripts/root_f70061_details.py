import struct,math,json
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0)
out=[]
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei; no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try: cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]
  except:continue
  if cnt>500 or po+hr+cnt*8>len(b) or po+dr+cnt*8>len(b):continue
  hs=[struct.unpack_from('<Q',b,po+hr+8*i)[0] for i in range(cnt)]; descs=[struct.unpack_from('<Q',b,po+dr+8*i)[0] for i in range(cnt)];
  # parse descriptor data rel / fmt
  ds=[]
  for i,desc_rel in enumerate(descs):
   d=po+desc_rel
   if d+16>len(b):ds.append(None);continue
   ds.append((struct.unpack_from('<I',b,d)[0],struct.unpack_from('<Q',b,d+8)[0],i,desc_rel))
  if 0x509903bb65ac341e not in hs:continue
  idx=hs.index(0x509903bb65ac341e);fmt,dp,_,desc_rel=ds[idx]; nextdp=min([x[1] for x in ds if x and x[1]>dp] or [ps]); nbytes=nextdp-dp;dat=po+dp;vals=[struct.unpack_from('<e',b,dat+2*k)[0] for k in range(nbytes//2)]
  if fmt!=0xf70061:continue
  # likely first 7 defaults then values; take first 96 samples and metadata tail 9
  seq=vals[7:-9] if len(vals)>=16 else vals[7:]
  out.append({'page':pi,'entry':ei,'channels':cnt,'idx':idx,'fmt':hex(fmt),'desc_rel':hex(desc_rel),'data_rel':hex(dp),'next_data_rel':hex(nextdp),'bytes':nbytes,'half_count':len(vals),'header':vals[:7],'samples':seq,'tail':vals[7+len(seq):]})
for x in out:
 print('p',x['page'],'e',x['entry'],'ch',x['channels'],'data',x['data_rel'],'next',x['next_data_rel'],'bytes',x['bytes'],'half',x['half_count'],'samples',len(x['samples']),'firstlast',x['samples'][:3],x['samples'][-3:],'tail',x['tail'])
json.dump(out,open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_f70061_details.json','w'),indent=2)
