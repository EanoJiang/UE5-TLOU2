import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\ellie-skel.pak';b=open(p,'rb').read();
for rs,size,name,typ in [(1058000,320,'group','group'),(3159264,120,'anim','anim'),(1056224,1056,'joint','joint')]:
 print('\n',name,rs)
 for off in range(0,size,8):
  if rs+off+8>len(b):break
  q=struct.unpack_from('<Q',b,rs+off)[0]
  print(f'{off:04x} {q:016x} u32={struct.unpack_from("<2I",b,rs+off)}')
