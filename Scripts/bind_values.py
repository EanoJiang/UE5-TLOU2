import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak'; b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);po,ps,_=struct.unpack_from('<3I',b,pt);n=struct.unpack_from('<H',b,po+18)[0]
for ei in range(n):
 q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro;cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0];print('E',ei)
 for i in range(cnt):
  h=struct.unpack_from('<Q',b,po+hr+8*i)[0];d=po+struct.unpack_from('<Q',b,po+dr+8*i)[0];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0]; vals=[struct.unpack_from('<e',b,po+dp+2*k)[0] for k in range(12)];print(i,hex(h),hex(fmt),vals)
