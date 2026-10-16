import struct, math
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);po,ps,_=struct.unpack_from('<3I',b,pt+2*12); q=po+20+4*16; rs=po+struct.unpack_from('<I',b,q+8)[0];cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0];
# channel0 descriptor
for idx in [0,1,2,3,4,5,6,7]:
 d=po+struct.unpack_from('<Q',b,po+dr+8*idx)[0];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0];
 # next data pointer
 dps=[]
 for i in range(cnt):
  dd=po+struct.unpack_from('<Q',b,po+dr+8*i)[0];dps.append((struct.unpack_from('<Q',b,dd+8)[0],i))
 nxt=min([x for x,i in dps if x>dp] or [ps]); vals=[struct.unpack_from('<e',b,po+dp+2*k)[0] for k in range((nxt-dp)//2)]
 print('idx',idx,'fmt',hex(fmt),'dp',hex(dp),'half',len(vals),'first30',vals[:30],'last30',vals[-30:])
