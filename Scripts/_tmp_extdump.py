import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();po=9541328
for rel in [0xac3b0,0x33dd0]:
 print('\nREL',hex(rel),'ABS',po+rel)
 raw=b[po+rel:po+rel+512]
 for i in range(0,512,16):print(f'{i:04x}',raw[i:i+16].hex(' '),[hex(struct.unpack_from('<I',raw,i+j)[0]) for j in range(0,16,4)])
