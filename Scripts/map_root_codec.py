import struct,math
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0)
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 # collect codecs
 hits=[];st=po
 while True:
  x=b.find(struct.pack('<I',0x41430102),st,po+ps)
  if x<0:break
  if x+44<=len(b):
   payload,g,fc=struct.unpack_from('<IHH',b,x+8); dt=struct.unpack_from('<f',b,x+36)[0]; rate=struct.unpack_from('<f',b,x+32)[0]; alt=struct.unpack_from('<f',b,x+40)[0]
   if payload<0x100000 and 0<fc<5000: hits.append((x-po, payload,g,fc,dt,rate,alt))
  st=x+4
 # raw resources root
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try:cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]
  except:continue
  if cnt>500 or po+hr+cnt*8>len(b) or po+dr+cnt*8>len(b):continue
  hs=[struct.unpack_from('<Q',b,po+hr+8*i)[0] for i in range(cnt)];descs=[struct.unpack_from('<Q',b,po+dr+8*i)[0] for i in range(cnt)]
  if 0x509903bb65ac341e not in hs:continue
  idx=hs.index(0x509903bb65ac341e);d=po+descs[idx];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0]
  if fmt not in [0xf70061,0xfb0050,0xfb005f,0xfb0088,0xfb0105]:continue
  # closest codec before data address
  bef=[h for h in hits if h[0]<=dp]; aft=[h for h in hits if h[0]>dp]; near=max(bef,key=lambda h:h[0]) if bef else None
  # correct relative data pointer to page, compare page relative
  print('page',pi,'entry',ei,'fmt',hex(fmt),'dp',hex(dp),'closestcodec',near,'next',aft[0] if aft else None)
