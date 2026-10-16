import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();po=9541328;rel=0x8e150
for o in [0,0x800,0x880,0x900,0x980,0xa00,0x880+2200]:
 raw=b[po+rel+o:po+rel+o+256];print('\nOFF',hex(o),raw[:64].hex(' '));print('u32',[hex(struct.unpack_from('<I',raw,4*i)[0]) for i in range(16)]);print('u64',[hex(struct.unpack_from('<Q',raw,8*i)[0]) for i in range(8)])
