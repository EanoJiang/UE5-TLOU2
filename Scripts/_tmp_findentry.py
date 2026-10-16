import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();h,hd,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]
def cs(o):e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else''
po,ps,_=pages[9]; ec=struct.unpack_from('<H',b,po+18)[0]
for ei in range(ec):
 no,ro=struct.unpack_from('<QI',b,po+20+16*ei)
 if 0x94fb0<=ro<=0xac500 or abs(ro-0xac3b0)<0x1000:
  rs=po+ro; print(ei,hex(ro),rs,cs(po+struct.unpack_from('<Q',b,rs)[0]),cs(po+struct.unpack_from('<Q',b,rs+8)[0]),'u32', [hex(struct.unpack_from('<I',b,rs+4*i)[0]) for i in range(12)])
