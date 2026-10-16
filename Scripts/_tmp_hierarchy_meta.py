import struct
p=r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak';b=open(p,'rb').read();base=15472
for rel in [0xfe1a0,0xfe1b0,0xfe260,0xfe3d0,0xfe410,0xfe460,0xfe490,0xfe4a0,0xfe8a0]:
 o=base+rel;raw=b[o:o+256];print('\nrel',hex(rel),'abs',o,'hex',raw[:128].hex(' '));print('u32',[hex(struct.unpack_from('<I',raw,4*i)[0]) for i in range(32)]);print('u64',[hex(struct.unpack_from('<Q',raw,8*i)[0]) for i in range(16)])
