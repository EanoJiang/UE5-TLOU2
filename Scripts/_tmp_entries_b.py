import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();h,hd,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)];po,ps,_=pages[9];ec=struct.unpack_from('<H',b,po+18)[0]
def cs(o):e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else''
for ei in range(ec):
 no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro; typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0]); name=cs(po+struct.unpack_from('<Q',b,rs)[0]);
 if 0x8d000<=ro<=0x92000:
  print(ei,hex(ro),rs,typ,repr(name), 'u32_12',hex(struct.unpack_from('<I',b,rs+48)[0]),'head',b[rs:rs+16].hex())
