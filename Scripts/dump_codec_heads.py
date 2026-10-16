import struct,os
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak']:
 b=open(p,'rb').read();magic,hdr,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]; print('\nFILE',os.path.basename(p))
 cnt=0
 for pi,(po,ps,fl) in enumerate(pages):
  ec=struct.unpack_from('<H',b,po+18)[0]; starts=[]
  for ei in range(ec):
   no,ro=struct.unpack_from('<QI',b,po+20+16*ei);starts.append((po+ro,ei,ro))
  for rs,ei,ro in starts:
   try:
    typoff=struct.unpack_from('<Q',b,rs+8)[0];e=b.find(b'\0',po+typoff);typ=b[po+typoff:e].decode()
   except:continue
   if typ!='ANIM':continue
   p1=struct.unpack_from('<Q',b,rs+56)[0];t=po+p1
   print('page',pi,'ei',ei,'rs',rs,'ANIMname?', '','v',struct.unpack_from('<II',b,rs+48),'ptr',hex(p1),'target',t,'head',b[t:t+64].hex())
   cnt+=1
   if cnt>=5:break
  if cnt>=5:break
