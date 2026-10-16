import struct,math,sys
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read(); po,ps,_=struct.unpack_from('<3I',b,44+2*12); q=po+20+4*16; rs=po+struct.unpack_from('<I',b,q+8)[0]; print('po',po,'rs',rs, 'q',q, 'entry',b[q:q+16].hex())
cnt=struct.unpack_from('<I',b,rs+48)[0];hrel=struct.unpack_from('<Q',b,rs+56)[0];drel=struct.unpack_from('<Q',b,rs+64)[0];print(cnt,hex(hrel),hex(drel))
for i in range(cnt):
 h=struct.unpack_from('<Q',b,po+hrel+8*i)[0];dr=struct.unpack_from('<Q',b,po+drel+8*i)[0];d=po+dr;fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0]; dat=po+dp
 vals=[struct.unpack_from('<e',b,dat+2*k)[0] for k in range(80) if dat+2*k+2<=len(b)]
 print(i,hex(h),hex(fmt),'desc',hex(dr),'data',hex(dp),'first',vals[:40])
