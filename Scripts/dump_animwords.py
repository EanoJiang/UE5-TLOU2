import struct
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; cb=b[s+16:]; po=struct.unpack_from('<3I',cb,44)[0]; no,ro=struct.unpack_from('<QI',cb,po+20); rs=po+ro
for off in range(rs,rs+240,4):
 print(f'{off-rs:03d} abs={off:06x} u32={struct.unpack_from("<I",cb,off)[0]:10d} i32={struct.unpack_from("<i",cb,off)[0]:10d} f={struct.unpack_from("<f",cb,off)[0]: .7g}')
