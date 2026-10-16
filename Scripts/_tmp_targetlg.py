import json,struct,collections
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();po=9541328; D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={f(x['name']):x for x in D['bones']}; joint=f('joint');
for rel,size,name in [(0x41750,2496,'codecA'),(0x8e150,0x30000,'streamB')]:
 raw=b[po+rel:po+rel+size];starts=[]
 for o in range(len(raw)-8):
  if struct.unpack_from('<Q',raw,o)[0]==joint:starts.append(o)
 hits=[]
 for o in range(len(raw)-8):
  x=struct.unpack_from('<Q',raw,o)[0]
  if x in by:hits.append((o,by[x]['name'],by[x]['index']))
 print(name,'len',len(raw),'jointmarkers',len(starts),starts[:20],'bonehashes',len(hits),'unique',len(set(x[1] for x in hits)));print(hits[:80])
