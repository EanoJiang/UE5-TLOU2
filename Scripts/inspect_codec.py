import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);po,ps,_=struct.unpack_from('<3I',b,pt+3*12)
for rel in [0x4de90,0x5f9f0,0x5b360,0x3c020]:
 p0=po+rel; print('rel',hex(rel), b[p0:p0+64].hex(' '));
 for off in range(0,52,4):print(off,hex(struct.unpack_from('<I',b,p0+off)[0]),struct.unpack_from('<f',b,p0+off)[0])
