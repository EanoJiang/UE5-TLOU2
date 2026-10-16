import pathlib,struct
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();po=9541328
for rel in [0xb41a0,0xbd580]:
 q=po+rel;print('\nREL',hex(rel),'abs',hex(q));
 for o in range(0,0x300,16):print(f'{o:03x}: '+b[q+o:q+o+16].hex(' '))
