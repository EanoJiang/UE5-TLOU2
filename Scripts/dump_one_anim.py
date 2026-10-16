import struct, json
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak'; b=open(p,'rb').read(); po=1088; rs=32960
for off in range(0,344,8):
 vals=struct.unpack_from('<Q',b,rs+off)[0]
 print(f'{off:03x} {vals:016x} u32={struct.unpack_from("<2I",b,rs+off)} f={struct.unpack_from("<2f",b,rs+off)}')
print('bytes after resource',b[rs:rs+344].hex())
