import struct,math,json
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();po,ps,_=struct.unpack_from('<3I',b,44+2*12);q=po+20+4*16;rs=po+struct.unpack_from('<I',b,q+8)[0];cnt=struct.unpack_from('<I',b,rs+48)[0];hrel=struct.unpack_from('<Q',b,rs+56)[0];drel=struct.unpack_from('<Q',b,rs+64)[0];
for i in range(cnt):
 h=struct.unpack_from('<Q',b,po+hrel+8*i)[0]; dr=struct.unpack_from('<Q',b,po+drel+8*i)[0]; d=po+dr;fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0]; dat=po+dp
 nextdp=None
 for j in range(cnt):
  if j==i:continue
  dj=po+struct.unpack_from('<Q',b,po+drel+8*j)[0];dpj=struct.unpack_from('<Q',b,dj+8)[0]
  if dpj>dp and (nextdp is None or dpj<nextdp): nextdp=dpj
 if nextdp is None: nextdp=ps
 nbytes=(nextdp-dp)
 vals=[struct.unpack_from('<e',b,dat+2*k)[0] for k in range(nbytes//2)]
 print(i,hex(h),hex(fmt),'dp',hex(dp),'next',hex(nextdp),'nbytes',nbytes,'halfcount',len(vals),'vals',vals if i==4 else '')
