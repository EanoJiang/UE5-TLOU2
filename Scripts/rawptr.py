import struct
b=open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak','rb').read();po,ps,_=struct.unpack_from('<3I',b,44+2*12);q=po+20+4*16;rs=po+struct.unpack_from('<I',b,q+8)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]; print(po,rs,hex(dr),dr)
for i in [4,5,6]:
 x=struct.unpack_from('<Q',b,po+dr+8*i)[0]; d=po+x; print(i,'desc rel',hex(x),'abs',d,'hdr',b[d:d+32].hex(' '),'fmt',hex(struct.unpack_from('<I',b,d)[0]),'dp',hex(struct.unpack_from('<Q',b,d+8)[0]))
