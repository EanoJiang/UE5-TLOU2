import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read();po,ps,_=struct.unpack_from('<3I',b,44+2*12);q=po+20+4*16;rs=po+struct.unpack_from('<I',b,q+8)[0];cnt=struct.unpack_from('<I',b,rs+48)[0];hrel=struct.unpack_from('<Q',b,rs+56)[0];drel=struct.unpack_from('<Q',b,rs+64)[0]; ds=[]
for i in range(cnt):
 d=po+struct.unpack_from('<Q',b,po+drel+8*i)[0];ds.append((struct.unpack_from('<Q',b,d+8)[0],i,struct.unpack_from('<I',b,d)[0]))
for x in sorted(ds): print(x)
