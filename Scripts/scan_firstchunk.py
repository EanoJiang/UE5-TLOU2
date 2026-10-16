import struct
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; nexts=b.find(b'ANIMMAGICSTR',s+16)-4; cb=b[s+16:nexts+16]; po=struct.unpack_from('<3I',cb,44)[0]; no,ro=struct.unpack_from('<QI',cb,po+20); rs=po+ro
print('cb len',len(cb),'page',po,'rs',rs)
for off in range(0,len(cb),16):
 if off>=rs+48 and off< len(cb):
  d=cb[off:off+16]
  if any(d): print(f'{off:04x}',d.hex(' '))
