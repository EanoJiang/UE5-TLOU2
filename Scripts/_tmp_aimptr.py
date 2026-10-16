import struct
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();h,hd,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]
def cs(o):e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else''
for pi,(po,ps,_) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(ec):
  no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro; typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0]); name=cs(po+struct.unpack_from('<Q',b,rs)[0])
  if typ!='ANIM' or 'prone-lg-aim-strafe' not in name:continue
  print(name,'page',pi,'entry',ei,'rel',hex(ro),'extA',hex(struct.unpack_from('<Q',b,rs+56)[0]),'extB',hex(struct.unpack_from('<Q',b,rs+64)[0]),'u32+52',struct.unpack_from('<I',b,rs+52)[0])
