import struct,pathlib
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();h=b[0x851cd0:0x851cd0+5456]
for o in range(0x50,0xc0,8): print(hex(o), [hex(x) for x in struct.unpack_from('<4H',h,o)], hex(struct.unpack_from('<Q',h,o)[0]))
