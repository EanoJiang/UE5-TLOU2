import struct,math
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0)
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 n=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(n):
  q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
  try:nptr,tptr=struct.unpack_from('<QQ',b,rs);name=b[po+nptr:b.find(b'\0',po+nptr)].decode();typ=b[po+tptr:b.find(b'\0',po+tptr)].decode()
  except:continue
  if typ!='ANIM':continue
  print(pi,ei,name,'+0x30',struct.unpack_from('<II',b,rs+48))
  vals=[]
  for off in range(0x70,0x120,4):
   try:f=struct.unpack_from('<f',b,rs+off)[0]
   except:continue
   if math.isfinite(f) and (f==0 or abs(f)<10000):vals.append((hex(off),f,struct.unpack_from('<I',b,rs+off)[0]))
  print(vals)
