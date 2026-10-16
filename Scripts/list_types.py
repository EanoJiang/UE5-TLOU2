import struct,collections
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);c=collections.Counter();
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei; no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try:tptr=struct.unpack_from('<Q',b,rs+8)[0];e=b.find(b'\0',po+tptr);typ=b[po+tptr:e].decode('utf8','replace'); nptr=struct.unpack_from('<Q',b,rs)[0];ne=b.find(b'\0',po+nptr);name=b[po+nptr:ne].decode('utf8','replace')
  except:continue
  c[(typ,name)]+=1
print('counts',c)
