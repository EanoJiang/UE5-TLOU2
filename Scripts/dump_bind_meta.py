import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak'; b=open(p,'rb').read();
for rs,size in [(35144,112),(35256,104),(35360,104),(35464,104),(35568,104),(35672,104),(35776,104),(35880,104),(36064,72)]:
 print('\nRS',rs,'size',size)
 for off in range(0,size,8):
  q=struct.unpack_from('<Q',b,rs+off)[0]; print(f'{off:03x} {q:016x} u32={struct.unpack_from("<2I",b,rs+off)} f={struct.unpack_from("<2f",b,rs+off)}')
