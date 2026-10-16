import pathlib
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak').read_bytes();
for q,sz in [(30816,1376),(26144,2336)]:
 print(hex(q),hex(q+sz));
 for o in range(max(0,sz-128),sz,16):print(f'{o:03x}: '+b[q+o:q+o+16].hex(' '))
