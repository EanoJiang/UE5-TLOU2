import json,struct,os
PAK=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak'; CAP=r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'; D=json.load(open(CAP));
def fnv(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={fnv(x['name']):x['name'] for x in D['bones']}; b=open(PAK,'rb').read(); po=9541328
for rel,size,name in [(0xac3b0,20000,'externalA'),(0x33dd0,20000,'externalB'),(0x41750,2496,'codec')]:
 bb=b[po+rel:po+rel+size];hits=[]
 for o in range(0,len(bb)-8):
  x=struct.unpack_from('<Q',bb,o)[0]
  if x in by:hits.append((o,hex(x),by[x]))
 print(name,'rel',hex(rel),'size',len(bb),'hits',len(hits),'unique',len(set(x[1] for x in hits)))
 print(hits[:200])
