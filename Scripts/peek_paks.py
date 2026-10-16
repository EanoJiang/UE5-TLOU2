import struct,os
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak']:
 b=open(p,'rb').read(); print(os.path.basename(p),len(b),b[:32].hex(' '));
 for sig in [b'ANIMMAGICSTR',b'ANIM\0',b'ANIM']:
  print(sig,[i for i in range(len(b)) if b.startswith(sig,i)][:5])
