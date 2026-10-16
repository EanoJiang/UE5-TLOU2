import json,struct
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json')); names=[x['name'] for x in D['bones']]
def f(d,seed=0xcbf29ce484222325):
 h=seed
 for x in d:h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
# hash variants
sets={}
for nm in names:
 for v in [nm,nm.lower(),nm.upper(),nm+'\0',nm.lower()+'\0']:
  for enc in ['utf-8','utf-16-le']:
   sets.setdefault(f(v.encode(enc)),[]).append((nm,repr(v),enc))
b=open(r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak','rb').read();base=15472
for rel,n in [(0x85490,26),(0x85630,64),(0x8ee80,400)]:
 print('\narray',hex(rel))
 for i in range(n):
  o=base+rel+16*i
  if o+16>len(b):break
  h,ptr=struct.unpack_from('<QQ',b,o)
  if h==0:continue
  print(i,hex(h),hex(ptr),sets.get(h,[])[:2])
