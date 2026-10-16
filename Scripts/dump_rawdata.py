import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak'; cb=open(p,'rb').read(); po=1088
for rel in [0x7cc8,0x7cf0,0x7d18,0x7d40,0x7d68,0x7d90,0x7db8,0x7dc8,0x7d28]:
 o=po+rel;print('rel',hex(rel),'abs',hex(o));print(' '.join(f'{x:02x}' for x in cb[o:o+96]));
 for i in range(0,96,16): print(' ',i,struct.unpack_from('<4f',cb,o+i))
