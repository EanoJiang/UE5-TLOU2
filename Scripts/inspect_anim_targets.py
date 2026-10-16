import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak'; b=open(p,'rb').read();po=1088
for rs in [35256,35360,35464,35568,35672,35776,35880]:
 print('\nANIM rs',rs)
 for o in [0x38,0x40]:
  ptr=struct.unpack_from('<Q',b,rs+o)[0];t=po+ptr;print(' ptr',hex(ptr),'target',t,'bytes',b[t:t+128].hex())
  for i in range(0,96,8):
   q=struct.unpack_from('<Q',b,t+i)[0];print(f'  {i:02x} {q:016x}',struct.unpack_from('<2f',b,t+i))
