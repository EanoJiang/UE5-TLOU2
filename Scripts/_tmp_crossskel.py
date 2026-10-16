import struct,glob,os
T=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e,0x05fed8d7a1d8cf89]
for p in glob.glob(r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\*-skel.pak'):
 b=open(p,'rb').read(); h=[]
 for x in T:
  q=b.find(struct.pack('<Q',x));
  if q>=0:h.append((hex(x),q))
 if h: print(os.path.basename(p),len(b),h)
