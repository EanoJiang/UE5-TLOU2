import pathlib,struct
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();q=0x9a77f0
for o in range(0,0x500,8):
 print(f'{o:03x}: {struct.unpack_from("<Q",b,q+o)[0]:016x}')
