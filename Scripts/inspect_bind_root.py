import struct,math
for path in [r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak',r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak']:
 b=open(path,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);print(path,fp)
 for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
  n=struct.unpack_from('<H',b,po+18)[0]
  for ei in range(n):
   q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
   try:cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]
   except:continue
   if cnt>2000 or po+hr+cnt*8>len(b) or po+dr+cnt*8>len(b):continue
   hs=[struct.unpack_from('<Q',b,po+hr+8*j)[0] for j in range(cnt)]; ds=[struct.unpack_from('<Q',b,po+dr+8*j)[0] for j in range(cnt)]
   if 0x509903bb65ac341e not in hs:continue
   idx=hs.index(0x509903bb65ac341e);d=po+ds[idx];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0];dat=po+dp; nxt=min([x[1] for x in [(0,dpj) for dpj in []]] or [ps]); vals=[struct.unpack_from('<e',b,dat+2*k)[0] for k in range(32)]
   print('p',pi,'e',ei,'cnt',cnt,'idx',idx,'fmt',hex(fmt),'datarel',hex(dp),'head',vals,'raw',b[dat:dat+32].hex(' '))
