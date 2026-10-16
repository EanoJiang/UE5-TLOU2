import struct,sys
p=r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak';b=open(p,'rb').read(); po=15472
for rel in [0x85490,0x85630,0x8ee80,0x92030,0xfe1a0,0xfe170,0x9235a,0x90000,0x91000]:
 o=po+rel;print('\nREL',hex(rel),'ABS',o,'hex',b[o:o+128].hex(' '));
 print('u32',[hex(struct.unpack_from('<I',b,o+4*i)[0]) for i in range(32)]);print('u64',[hex(struct.unpack_from('<Q',b,o+8*i)[0]) for i in range(16)])
