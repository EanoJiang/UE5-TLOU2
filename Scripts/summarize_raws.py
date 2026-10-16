import struct
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak']:
 b=open(p,'rb').read();magic,hdr,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]; print('\n',p)
 for pi,(po,ps,fl) in enumerate(pages):
  ec=struct.unpack_from('<H',b,po+18)[0]; starts=[]
  for ei in range(ec):
   q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);starts.append((po+ro,ei,ro))
  for idx,(rs,ei,ro) in enumerate(starts):
   if rs+56>len(b):continue
   try: typoff=struct.unpack_from('<Q',b,rs+8)[0];e=b.find(b'\0',po+typoff);typ=b[po+typoff:e].decode('utf8')
   except:continue
   if typ!='ANIM_RAWCHANNELS':continue
   nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps]);size=nxt-rs
   count=struct.unpack_from('<I',b,rs+48)[0]; p1=struct.unpack_from('<Q',b,rs+56)[0]; p2=struct.unpack_from('<Q',b,rs+64)[0]
   hashes=[]
   for j in range(min(count,20)): hashes.append(struct.unpack_from('<Q',b,rs+72+8*j)[0])
   print('pi',pi,'ei',ei,'rs',rs,'size',size,'count',count,'p1',hex(p1),'p2',hex(p2),'hash0', [hex(x) for x in hashes[:5]])
