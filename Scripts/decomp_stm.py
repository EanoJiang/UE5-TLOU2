import zlib,glob,os,struct
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read();
for sig in [b'\x78\x9c',b'\x78\xda']:
 i=0
 while True:
  i=b.find(sig,i)
  if i<0:break
  for wbits in [15,-15,31]:
   try:
    d=zlib.decompress(b[i:],wbits); print('off',i,'sig',sig.hex(),'wb',wbits,'dlen',len(d), 'head',d[:64].hex(' '));break
   except Exception as e:
    pass
  i+=1
