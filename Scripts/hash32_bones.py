import bpy,struct,zlib
names=[b.name for a in bpy.data.armatures for b in a.bones]
targets=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
def fnv32(s):
 h=0x811c9dc5
 for c in s:h=((h^c)*0x01000193)&0xffffffff
 return h
def mur3(s,seed=0):
 h=seed; n=len(s); i=0
 while n-i>=4:
  k=int.from_bytes(s[i:i+4],'little'); k=(k*0xcc9e2d51)&0xffffffff;k=((k<<15)|(k>>17))&0xffffffff;k=(k*0x1b873593)&0xffffffff;h^=k;h=((h<<13)|(h>>19))&0xffffffff;h=(h*5+0xe6546b64)&0xffffffff;i+=4
 k=0;rem=s[i:]
 if len(rem)==3:k^=rem[2]<<16
 if len(rem)>=2:k^=rem[1]<<8
 if len(rem)>=1:k^=rem[0];k=(k*0xcc9e2d51)&0xffffffff;k=((k<<15)|(k>>17))&0xffffffff;k=(k*0x1b873593)&0xffffffff;h^=k
 h^=len(s);h^=h>>16;h=(h*0x85ebca6b)&0xffffffff;h^=h>>13;h=(h*0xc2b2ae35)&0xffffffff;h^=h>>16;return h
for var,ns in [('orig',names),('lower',[x.lower() for x in names]),('upper',[x.upper() for x in names])]:
 for fn,func in [('fnv32',fnv32),('crc',lambda x:zlib.crc32(x)&0xffffffff),('m3',mur3)]:
  hits=[]
  for nm in ns:
   v=func(nm.encode());
   for t in targets:
    if v in [t&0xffffffff,t>>32]:hits.append((nm,hex(v),hex(t)))
  if hits:print(var,fn,hits)
