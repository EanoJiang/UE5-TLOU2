import itertools
T=0x53de1e1977f9cba4

def fnv1a(d,seed=0xcbf29ce484222325):
 h=seed
 for x in d:h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
parts=['anim-ellie-player-bindpose','anim-ellie-player-movement','bindpose','movement','ANIM_GROUP','anim_group','ellie','player','root','Ellie','ellie-player','anim-ellie-player']
for p in parts:
 for v in [p,p.lower(),p.upper(),p+'\0','/'+p,p.replace('-','_'),p.replace('-','/'),p.replace('-','.')]:
  for enc in ['utf8','utf-16le']:
   x=fnv1a(v.encode(enc))
   if x==T:print('hit',repr(v),enc)
   print(repr(v),enc,hex(x))
