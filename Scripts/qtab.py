import struct
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; e=b.find(b'ANIMMAGICSTR',s+16)-4; cb=b[s+16:e+16]
for o in range(0x100,0x220,8): print(f'{o:04x}: {struct.unpack_from("<Q",cb,o)[0]:016x} ({struct.unpack_from("<I",cb,o)[0]:08x} {struct.unpack_from("<I",cb,o+4)[0]:08x})')
