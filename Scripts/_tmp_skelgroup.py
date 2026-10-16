import struct
p=r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak';b=open(p,'rb').read();po=15472
o=po+0xfe860; raw=b[o:o+640];print(raw[:200].hex(' '));
for off in range(0,640,8):
 q=struct.unpack_from('<Q',raw,off)[0]
 if 0<q<1048176:
  t=po+q;e=b.find(b'\0',t);st=b[t:e].decode('utf8','replace') if e>=0 else''
  print(off,hex(q),'abs',t,'str',repr(st[:100]))
print('u32', [hex(struct.unpack_from('<I',raw,4*i)[0]) for i in range(80)])
