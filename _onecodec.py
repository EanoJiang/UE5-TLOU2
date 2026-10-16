import pathlib,struct,json
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();q=0x851cd0;h=b[q:q+5456]
for o in range(0x30,0x110,16): print(f'{o:03x}: '+h[o:o+16].hex(' '))
