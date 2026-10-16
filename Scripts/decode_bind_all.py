import struct,json,os
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak';b=open(p,'rb').read(); po=1088
resources=[32960,33304,33648,33992,34336,34680,35024]
for ri,rs in enumerate(resources):
 size=344 if ri<6 else 120; c=struct.unpack_from('<I',b,rs+48)[0]; print('\nRAW',ri,'count',c)
 hashes=[struct.unpack_from('<Q',b,rs+72+8*i)[0] for i in range(c)]; ptrs=[struct.unpack_from('<Q',b,rs+72+8*c+8*i)[0] for i in range(c)]
 print('hashes',[hex(x) for x in hashes]); print('ptrs',[hex(x) for x in ptrs])
 # descriptor bases = page offset ptrs + po
 for j,ptr in enumerate(ptrs):
  d=po+ptr; fmt=struct.unpack_from('<I',b,d)[0]; dp=struct.unpack_from('<Q',b,d+8)[0]; st=po+dp
  # until next descriptor or resource end
  nextd=min([po+x for x in ptrs if po+x>d]+[rs+size]); data=b[st:nextd]
  half=[]
  for o in range(0,len(data)-1,2): half.append(struct.unpack_from('<e',data,o)[0])
  print(j,'fmt',hex(fmt),'d',hex(d),'dp',hex(dp),'len',len(data),'half',half[:16])
