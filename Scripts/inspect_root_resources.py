import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0); wanted={(3,3),(3,2),(3,1),(1,1)}
for pi,ei in wanted:
 po,ps,_=struct.unpack_from('<3I',b,pt+12*pi);q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro;cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]; print('\npage',pi,'entry',ei,'cnt',cnt)
 for i in range(cnt):
  h=struct.unpack_from('<Q',b,po+hr+8*i)[0];desc=po+struct.unpack_from('<Q',b,po+dr+8*i)[0];fmt=struct.unpack_from('<I',b,desc)[0];dp=struct.unpack_from('<Q',b,desc+8)[0]; print(i,hex(h),hex(fmt),'data',hex(dp))
