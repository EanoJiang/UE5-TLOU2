import json
# manually parse list from data as in prior script and detect values
import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();po,ps,_=struct.unpack_from('<3I',b,44+2*12);q=po+20+4*16;rs=po+struct.unpack_from('<I',b,q+8)[0];hrel=struct.unpack_from('<Q',b,rs+56)[0];drel=struct.unpack_from('<Q',b,rs+64)[0];dr=struct.unpack_from('<Q',b,po+drel+8*4)[0];d=po+dr;dp=struct.unpack_from('<Q',b,d+8)[0]; vals=[struct.unpack_from('<e',b,po+dp+2*k)[0] for k in range(112)]
for i,v in enumerate(vals): print(i,v)
print('header',vals[:7]); x=vals[7:];
for i,v in enumerate(x):
 if abs(v)>1e-2: print('s',i,v)
print('len x',len(x),'angle monotonic before trailing')
