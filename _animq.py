import pathlib,struct,json
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();q=0x9d5070
for o in range(0,0x300,8):
 v=struct.unpack_from('<Q',b,q+o)[0]
 print(f'{o:03x} {v:016x}',end='  ')
 if o%0x40==0x38: print()
