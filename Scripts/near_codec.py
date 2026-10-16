import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read();_,_,_,_,_,pt,pc,*_=struct.unpack_from('<11I',b,0)
for pi,dp in [(3,0x87fc8),(3,0x76eb8),(3,0x544f8),(6,0x28120),(1,0x9f898)]:
 po,ps,_=struct.unpack_from('<3I',b,pt+12*pi); hits=[];st=po
 while 1:
  x=b.find(struct.pack('<I',0x41430102),st,po+ps)
  if x<0:break
  payload=struct.unpack_from('<I',b,x+8)[0];fc=struct.unpack_from('<H',b,x+14)[0];period=struct.unpack_from('<f',b,x+44)[0];rate=struct.unpack_from('<f',b,x+28)[0]
  start=x-po;end=start+0x30+payload
  hits.append((start,end,payload,fc,period,rate))
  st=x+4
 near=min(hits,key=lambda h:abs(dp-h[0]))
 print('target',pi,hex(dp),'near',tuple(hex(x) if i<2 else x for i,x in enumerate(near)),'dp in?',[(hex(x[0]),hex(x[1])) for x in hits if x[0]<=dp<=x[1]][:3])
