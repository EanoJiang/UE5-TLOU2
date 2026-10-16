import struct,glob,os
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; nexts=b.find(b'ANIMMAGICSTR',s+16)-4; cb=b[s+16:nexts+16]; po=struct.unpack_from('<3I',cb,44)[0]; ro=struct.unpack_from('<QI',cb,po+20)[1]; rs=po+ro
for off in range(0,224,8):
 q=rs+off; print(f'{off:03d} {q:06x}: Q={struct.unpack_from("<Q",cb,q)[0]:016x} I={struct.unpack_from("<I",cb,q)[0]:08x} {struct.unpack_from("<I",cb,q+4)[0]:08x}')
