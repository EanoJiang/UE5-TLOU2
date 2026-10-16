import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0)
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei; no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try: cnt=struct.unpack_from('<I',b,rs+48)[0]; hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]
  except: continue
  if cnt>500: continue
  hs=[struct.unpack_from('<Q',b,po+hr+8*i)[0] for i in range(cnt)];ds=[struct.unpack_from('<Q',b,po+dr+8*i)[0] for i in range(cnt)]
  if 0x509903bb65ac341e not in hs: continue
  idx=hs.index(0x509903bb65ac341e);d=po+ds[idx];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0]
  if fmt==0xf70061:
   nn=min([x for x in ds if x>dp] or [ps]); print('found',pi,ei,'rs',rs,'idx',idx,'dp',hex(dp),dp,'next',hex(nn),nn,'diff',nn-dp,'ds around',[(i,hex(x)) for i,x in enumerate(ds) if dp-1000<x<dp+1000]);
