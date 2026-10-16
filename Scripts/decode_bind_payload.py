import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak'; b=open(p,'rb').read(); rs=32960
for idx,base in enumerate([0x98,0xc0,0xe8,0x110,0x138]):
 abs=rs+base; fmt=struct.unpack_from('<I',b,abs)[0]; ptr=struct.unpack_from('<Q',b,abs+8)[0]; ds=rs+0xa8+0x28*idx # guessed? actual payload starts +0xa8 + 0x28 each? 
 # locate next descriptor base
 nextb=[0xc0,0xe8,0x110,0x138,0x160][idx]
 data=b[abs+16:rs+nextb]
 print('\nchannel',idx,'desc',hex(abs),'fmt',hex(fmt),'ptr',hex(ptr),'payload',len(data),data.hex())
 print('halfs',[struct.unpack_from('<e',data,i)[0] for i in range(0,len(data)-1,2)])
 print('u16',[hex(struct.unpack_from('<H',data,i)[0]) for i in range(0,len(data)-1,2)])
