import struct,collections
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);print('pages',fp)
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 n=struct.unpack_from('<H',b,po+18)[0];print('page',pi,'n',n)
 for ei in range(min(n,20)):
  q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try:cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0];hs=[struct.unpack_from('<Q',b,po+hr+8*j)[0] for j in range(cnt)];ds=[struct.unpack_from('<Q',b,po+dr+8*j)[0] for j in range(cnt)];
  except:continue
  if 0x509903bb65ac341e not in hs:continue
  idx=hs.index(0x509903bb65ac341e);d=po+ds[idx];fmt=struct.unpack_from('<I',b,d)[0];print(' e',ei,'cnt',cnt,'idx',idx,'hashes',[hex(x) for x in hs],'fmt',hex(fmt))
