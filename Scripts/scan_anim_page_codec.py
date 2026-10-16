import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);po,ps,_=struct.unpack_from('<3I',b,pt+6*12);rs=po+0x31be0
for base in [0x39060,0x70740,0x31c48,0x31c60,0x32938]:
 abs=po+base; print('base',hex(base),'abs',abs,'bytes',b[abs:abs+128].hex(' '));
 for off in range(0,128,4):
  u=struct.unpack_from('<I',b,abs+off)[0]; f=struct.unpack_from('<f',b,abs+off)[0]; print(f'{off:02x}:{u:08x}/{f:.7g}',end=' ')
 print()
# find codec magic in page6
m=struct.pack('<I',0x41430102)
pos=[];st=po
while True:
 i=b.find(m,st,po+ps)
 if i<0:break
 pos.append(i-po);st=i+1
print('codec hits',len(pos),[hex(x) for x in pos[:20]])
for x in pos[:10]:
 p0=po+x;print(hex(x),b[p0:p0+64].hex(' '),[struct.unpack_from('<I',b,p0+4*j)[0] for j in range(12)])
