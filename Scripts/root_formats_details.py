import struct,math,json,collections
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0); wanted={0xf70061,0xfb0050,0xfb005f,0xfb0088,0xfb0105}
out=[]
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei; no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try:cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]
  except:continue
  if cnt>500 or po+hr+cnt*8>len(b) or po+dr+cnt*8>len(b):continue
  hs=[struct.unpack_from('<Q',b,po+hr+8*i)[0] for i in range(cnt)];descs=[struct.unpack_from('<Q',b,po+dr+8*i)[0] for i in range(cnt)];ds=[]
  for i,desc_rel in enumerate(descs):
   d=po+desc_rel
   if d+16>len(b):ds.append(None);continue
   ds.append((struct.unpack_from('<I',b,d)[0],struct.unpack_from('<Q',b,d+8)[0],i,desc_rel))
  for idx,(h) in enumerate(hs):
   if h!=0x509903bb65ac341e:continue
   fmt,dp,_,desc_rel=ds[idx]
   if fmt not in wanted:continue
   ndp=min([x[1] for x in ds if x and x[1]>dp] or [ps]); nbytes=ndp-dp; vals=[struct.unpack_from('<e',b,po+dp+2*k)[0] for k in range(nbytes//2)]
   # dynamic streams likely baseline 7, stream until metadata tail9; determine pair group count
   # all target have tail 9 per known format; assume trim
   stream=vals[7:-9] if len(vals)>=16 else vals[7:]; tail=vals[7+len(stream):]
   out.append(dict(page=pi,entry=ei,channels=cnt,idx=idx,format=hex(fmt),desc_rel=hex(desc_rel),data_rel=hex(dp),next_data_rel=hex(ndp),payload_bytes=nbytes,half_count=len(vals),header=vals[:7],stream_half_count=len(stream),stream_values=stream,tail=tail))
for x in out:
 arity=1 if x['format']=='0xf70061' else 2
 print('p',x['page'],'e',x['entry'],'fmt',x['format'],'data',x['data_rel'],'bytes',x['payload_bytes'],'half',x['half_count'],'stream',x['stream_half_count'],'samples',x['stream_half_count']//arity,'rem',x['stream_half_count']%arity,'header',x['header'],'first',x['stream_values'][:8],'last',x['stream_values'][-8:],'tail',x['tail'])
json.dump(out,open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_formats_details.json','w'),indent=2)
