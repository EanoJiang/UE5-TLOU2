import struct,math,collections
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0)
for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(fp)]):
 hits=[];st=po
 while True:
  x=b.find(struct.pack('<I',0x41430102),st,po+ps)
  if x<0:break
  # parse header 52 bytes
  if x+52<=len(b):
   payload, g,fc=struct.unpack_from('<IHH',b,x+8); dt=struct.unpack_from('<f',b,x+36)[0]; fc2=struct.unpack_from('<H',b,x+34)[0]; rate=struct.unpack_from('<f',b,x+40)[0]; h=struct.unpack_from('<I',b,x+4)[0]
   if payload<0x100000 and 0<fc<10000:
    hits.append((x-po,payload,g,fc,dt,fc2,rate,h))
  st=x+4
 print('PAGE',pi,'hits',len(hits))
 for h in hits[:120]:print(' ',hex(h[0]),'payload',h[1],'g',h[2],'fc',h[3],'dt',h[4],'fc2',h[5],'rate',h[6],'hash',hex(h[7]))
