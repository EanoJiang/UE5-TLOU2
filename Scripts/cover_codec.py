import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0)
for pi,ei,dp in [(3,3,0x87fc8),(3,2,0x76eb8),(3,1,0x544f8),(6,11,0x28120),(1,1,0x9f898)]:
 po,ps,_=struct.unpack_from('<3I',b,pt+12*pi); hits=[];st=po
 while 1:
  x=b.find(struct.pack('<I',0x41430102),st,po+ps)
  if x<0:break
  payload=struct.unpack_from('<I',b,x+8)[0];fc=struct.unpack_from('<H',b,x+14)[0];period=struct.unpack_from('<f',b,x+44)[0]; rate=struct.unpack_from('<f',b,x+28)[0]
  start=x-po; end=start+0x30+payload
  if start<=dp<end: hits.append((hex(start),hex(end),payload,fc,period,rate))
  st=x+4
 print('target',pi,ei,hex(dp),'cover',hits)
