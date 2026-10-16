import glob,os
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read();
for off in [11026,20197,73954,37450]: print(off,b[off:off+64].hex(' '))
