import struct,math,os
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]
for pi,(po,ps,_) in enumerate(pages):
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei; no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try:nptr,tptr=struct.unpack_from('<QQ',b,rs); ne=b.find(b'\0',po+nptr);te=b.find(b'\0',po+tptr);name=b[po+nptr:ne].decode();typ=b[po+tptr:te].decode()
  except:continue
  if typ!='ANIM':continue
  print('\nANIM p',pi,'e',ei,'name',name,'rs',rs,'po',po,'size',ps,'rel',ro)
  print('head',b[rs:rs+256].hex(' '))
  for off in range(0,256,8):
   v=struct.unpack_from('<Q',b,rs+off)[0]; u=struct.unpack_from('<I',b,rs+off)[0]; f=struct.unpack_from('<f',b,rs+off)[0]
   if v and v < ps: print(' off',hex(off),'u',hex(u),'q',hex(v),'target',hex(po+v),'f',f, 'tbytes',b[po+v:po+v+32].hex(' '))
