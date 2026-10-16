import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read(); po=9541328
for o in [po+0x94fb0,po+0x95a80,po+0x95fe0,po+0x96540]:
 print('\nABS',o,'REL',hex(o-po)); raw=b[o:o+180]; print(raw.hex(' '));
 print('u32',[hex(struct.unpack_from('<I',raw,4*i)[0]) for i in range(45)]); print('u64',[hex(struct.unpack_from('<Q',raw,8*i)[0]) for i in range(22)])
