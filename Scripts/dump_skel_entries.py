import struct,os
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\ellie-skel.pak']:
 b=open(p,'rb').read(); print('file',len(b),b[:64].hex()); magic,hdr,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]; print('pages',pages)
 def cs(o): e=b.find(b'\0',o);return b[o:e].decode('utf8','replace')
 for pi,(po,ps,f) in enumerate(pages):
  ec=struct.unpack_from('<H',b,po+18)[0]; print('page',pi,po,ps,ec)
  for ei in range(ec):
   q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q); rs=po+ro
   try:name=cs(po+struct.unpack_from('<Q',b,rs)[0]); typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0])
   except:continue
   print(ei,'ro',ro,'rs',rs,'name',name,'type',typ)
   if typ=='JOINT_HIERARCHY':
    print('head',b[rs:rs+256].hex())
