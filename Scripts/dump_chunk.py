import struct
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; nexts=b.find(b'ANIMMAGICSTR',s+16)-4; cb=b[s+16:nexts+16]
# print runs of repeated zero / random etc at each 64 bytes
for off in range(0, len(cb),64):
 d=cb[off:off+64]
 print(f'{off:04x}',d.hex(' '))
