import json,pathlib,struct
cap=json.loads(pathlib.Path('Exports/ExactDebug/ellie16_patrol_body/capture.json').read_text());
def fnv(s):
 h=0xcbf29ce484222325
 for c in s.encode():h=((h^c)*0x100000001b3)&0xffffffffffffffff
 return h
hs={fnv(x['name']):x['name'] for x in cap['bones']};print('hashes',len(hs),list(hs.items())[:3])
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();regions=[('codec',0x95ae20,2496),('anim',0x9d5070,4096),('raw',0x9a77f0,0x500)]
for nm,q,n in regions:
 hits=[]
 for o in range(0,n-8):
  v=struct.unpack_from('<Q',b,q+o)[0]
  if v in hs:hits.append((o,v,hs[v]))
 print(nm,'hits',len(hits),[(hex(o),hex(v),s) for o,v,s in hits[:30]])
