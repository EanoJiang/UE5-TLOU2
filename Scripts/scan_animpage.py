import struct,glob,os
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read(); s=b.find(b'ANIMMAGICSTR')-4; cb=b[s+16:]; po=struct.unpack_from('<3I',cb,44)[0]; no,ro=struct.unpack_from('<QI',cb,po+20); rs=po+ro
# print all recognized strings and where
for m in __import__('re').finditer(rb'[ -~]{4,}\x00',cb):
 st=m.group()[:-1];
 if any(k in st for k in [b'ANIM',b'RAW',b'PAK',b'VRAM',b'ice',b'dina',b'chunk']): print(m.start(),st)
print('length',len(cb),'rs',rs)
# scan words around end in 4 bytes
for off in range(max(0,len(cb)-1024),len(cb),16): print(f'{off:06x}',cb[off:off+16].hex(' '))
