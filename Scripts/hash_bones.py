import bpy,struct,math
names=[]
for a in bpy.data.armatures:
 names=[b.name for b in a.bones]; break
targets=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
# funcs
def fnv1a(s,seed=0xcbf29ce484222325):
 h=seed
 for c in s: h=((h^c)*0x100000001b3)&0xffffffffffffffff
 return h
def fnv1(s,seed=0xcbf29ce484222325):
 h=seed
 for c in s: h=(h*0x100000001b)&0xffffffffffffffff; h ^= c
 return h
def murmur64a(data,seed=0):
 m=0xc6a4a7935bd1e995; r=47; n=len(data); h=(seed ^ ((n*m)&0xffffffffffffffff)) & 0xffffffffffffffff
 # qwords little
 for i in range(0,n//8*8,8):
  k=int.from_bytes(data[i:i+8],'little'); k=(k*m)&0xffffffffffffffff; k ^= k>>r; k=(k*m)&0xffffffffffffffff; h ^= k; h=(h*m)&0xffffffffffffffff
 t=data[n//8*8:];
 if len(t)==7:h^=t[6]<<48
 if len(t)>=6:h^=t[5]<<40
 if len(t)>=5:h^=t[4]<<32
 if len(t)>=4:h^=t[3]<<24
 if len(t)>=3:h^=t[2]<<16
 if len(t)>=2:h^=t[1]<<8
 if len(t)>=1:h^=t[0];h=(h*m)&0xffffffffffffffff
 h^=h>>r;h=(h*m)&0xffffffffffffffff;h^=h>>r
 return h
def murmur64b(data,seed=0):
 # MurmurHash64B x86 two uint32
 import struct
 m=0x5bd1e995; r=24; n=len(data); h1=(seed ^ n)&0xffffffff; h2=seed&0xffffffff; i=0
 while n>=8:
  k1=int.from_bytes(data[i:i+4],'little'); k1=(k1*m)&0xffffffff;k1^=k1>>r;k1=(k1*m)&0xffffffff;h1=(h1*m)&0xffffffff;h1^=k1;i+=4;n-=4
  k2=int.from_bytes(data[i:i+4],'little'); k2=(k2*m)&0xffffffff;k2^=k2>>r;k2=(k2*m)&0xffffffff;h2=(h2*m)&0xffffffff;h2^=k2;i+=4;n-=4
 if n>=4:
  k1=int.from_bytes(data[i:i+4],'little'); k1=(k1*m)&0xffffffff;k1^=k1>>r;k1=(k1*m)&0xffffffff;h1=(h1*m)&0xffffffff;h1^=k1;i+=4;n-=4
 if n==3:h2^=data[i+2]<<16
 if n>=2:h2^=data[i+1]<<8
 if n>=1:h2^=data[i];h2=(h2*m)&0xffffffff
 h1^=h2>>18;h1=(h1*m)&0xffffffff;h2^=h1>>22;h2=(h2*m)&0xffffffff;h1^=h2>>17;h1=(h1*m)&0xffffffff;h2^=h1>>19;h2=(h2*m)&0xffffffff
 return (h1<<32)|h2
def djb2(s):
 h=5381
 for c in s:h=((h*33)^c)&0xffffffffffffffff
 return h
def jenkins(s):
 h=0
 for c in s:h=(h+c)&0xffffffffffffffff;h=(h+(h<<10))&0xffffffffffffffff;h ^= h>>6
 h=(h+(h<<3))&0xffffffffffffffff;h ^= h>>11;h=(h+(h<<15))&0xffffffffffffffff
 return h
funcs={"fnv1a":fnv1a,"fnv1":fnv1,"murmur64a":murmur64a,"murmur64b":murmur64b,"djb2":djb2,"jenkins":jenkins}
variants={}
for nm in names:
 for var,s in [('orig',nm),('lower',nm.lower()),('upper',nm.upper()),('nul',nm+'\0'),('lowernul',nm.lower()+'\0')]:variants.setdefault(var,[]).append(s.encode())
for fn,func in funcs.items():
 for var in ['orig','lower','upper','nul','lowernul']:
  vals=[func(x) for x in variants[var]]
  hits=[names[i] for i,v in enumerate(vals) if v in targets]
  if hits:print(fn,var,hits)
 # seeds common
 for seed in [0,1,0x9747b28c,0xc70f6907]:
  hits=[]
  for i,nm in enumerate(names):
   x=(nm.lower()).encode();
   try:v=func(x,seed)
   except:continue
   if v in targets:hits.append((nm,hex(seed)))
  if hits: print(fn,'seed',hits)
print('targets', [hex(x) for x in targets]); print('names',len(names))
