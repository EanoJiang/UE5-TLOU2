import json,struct,collections
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();po=9541328
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={f(x['name']):(x['index'],x['name']) for x in D['bones']}
for rel,size,name in [(0xac3b0,0x180,'A_prefix'),(0xac3b0,0x18000,'A_big'),(0x33dd0,0x20000,'B_big')]:
 raw=b[po+rel:po+rel+size]; print('\n',name,'rel',hex(rel),'size',len(raw))
 hits=[]
 for o in range(0,len(raw)-8):
  x=struct.unpack_from('<Q',raw,o)[0]
  if x in by:hits.append((o,hex(x),by[x]))
 print('count',len(hits),'unique',len(set(x[1] for x in hits)))
 # group offsets by mod 48/16
 mods=collections.Counter(o%48 for o,_,_ in hits); print('mods48',mods)
 for h in hits[:200]:print(h)
