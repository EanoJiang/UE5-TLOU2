import struct
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; e=b.find(b'ANIMMAGICSTR',s+16)-4; cb=b[s+16:e+16]
for val in [0x110,0x100,0x0,0x18d0,0x1930,0x1a10,0x1a16,0x1a2f,0x1a49,0x1a11]:
 print('VAL',hex(val));
 for o in range(0,len(cb)-8,8):
  if struct.unpack_from('<Q',cb,o)[0]==val: print(hex(o))
