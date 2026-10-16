import struct,glob,os
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read();
i=b.find(b'ANIMMAGICSTR'); s=i-4; cb=b[s+16:]
magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',cb,0); po=struct.unpack_from('<3I',cb,pt)[0]
# first page entry at po+20
no,ro=struct.unpack_from('<QI',cb,po+20); rs=po+ro
print('s',s,'po',po,'ro',ro,'rs',rs,'page size',len(cb))
for o in range(rs,rs+512,16): print(f'{o:06x}', cb[o:o+16].hex(' '))
