import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read(); t=6692640
for o in range(0,240,4):
 q=struct.unpack_from('<I',b,t+o)[0]; f=struct.unpack_from('<f',b,t+o)[0]
 print(f'{o:03x} {q:08x} {q:10d} f={f: .8g}')
