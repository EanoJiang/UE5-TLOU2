import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();po=9541328
for rel in [0x95018,0x95030,0x95198,0x951d8,0x95038,0x95048,0xac3b0,0x33dd0]:
 o=po+rel;raw=b[o:o+256]; print('\nREL',hex(rel),'ABS',o,raw.hex(' '));print('u32',[hex(struct.unpack_from('<I',raw,4*i)[0]) for i in range(32)]);print('u64',[hex(struct.unpack_from('<Q',raw,8*i)[0]) for i in range(16)])
