# parse direct PAK resource item and dump names/fields
import struct,os,re
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak']:
 cb=open(p,'rb').read(); print('\n',os.path.basename(p),len(cb));
 magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',cb,0); print('hdr',magic,hdr,li,lo,pct,pt,fp,fo)
 pages=[struct.unpack_from('<3I',cb,pt+p*12) for p in range(pct)]; print('pages',pages)
 for pi,(po,ps,_) in enumerate(pages):
  n=struct.unpack_from('<H',cb,po+18)[0]; print('page',pi,po,ps,n)
  for j in range(n):
   q=po+20+j*16; no,ro=struct.unpack_from('<QI',cb,q); rs=po+ro; itype='';
   def cstr(o):
    e=cb.find(b'\0',o); return cb[o:e].decode('utf8','replace')
   try:
    iname=cstr(po+struct.unpack_from('<Q',cb,rs)[0]); itype=cstr(po+struct.unpack_from('<Q',cb,rs+8)[0])
   except: iname='';
   print(' ',j,'name',iname,'type',itype,'rs',rs,'ro',ro)
   if itype=='ANIM':
    for off in range(0,224,8):
      q=rs+48+off; print(f'  {off:03x}: {struct.unpack_from("<Q",cb,q)[0]:016x}')
