import struct,os,math
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak']:
 b=open(p,'rb').read();magic,hdr,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)];print('\n',os.path.basename(p))
 total=0
 for pi,(po,ps,fl) in enumerate(pages):
  ec=struct.unpack_from('<H',b,po+18)[0];starts=[]
  for ei in range(ec):
   no,ro=struct.unpack_from('<QI',b,po+20+16*ei);starts.append((po+ro,ei,ro))
  for rs,ei,ro in starts:
   try:to=struct.unpack_from('<Q',b,rs+8)[0];e=b.find(b'\0',po+to);typ=b[po+to:e].decode()
   except:continue
   if typ!='ANIM_RAWCHANNELS':continue
   nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps]);size=nxt-rs;c=struct.unpack_from('<I',b,rs+48)[0]
   hashes=[struct.unpack_from('<Q',b,rs+72+8*i)[0] for i in range(c)];ptrs=[struct.unpack_from('<Q',b,rs+72+8*c+8*i)[0] for i in range(c)]
   if 0x509903bb65ac341e not in hashes:continue
   j=hashes.index(0x509903bb65ac341e); d=po+ptrs[j];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0];st=po+dp; nextd=min([po+x for x in ptrs if po+x>d]+[rs+size]);data=b[st:nextd]
   hs=[]
   for k in range(0,len(data)-1,2):
    try:x=struct.unpack_from('<e',data,k)[0]; hs.append(x)
    except:pass
   print('pi',pi,'ei',ei,'rs',rs,'size',size,'count',c,'j',j,'fmt',hex(fmt),'data_len',len(data),'half first',hs[:40],'bytes',data[:64].hex())
   total+=1
   if total>=20:break
  if total>=20:break
