import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\ellie-skel.pak';b=open(p,'rb').read();
for rs,size in [(1057280,720),(1058640,344),(1058984,344),(1059328,344),(1059672,344),(1060016,344),(1060360,344),(1060704,296)]:
 print('\nRS',rs,'size',size)
 print('u32', [struct.unpack_from('<I',b,rs+4*i)[0] for i in range(0,min(size,256)//4)])
