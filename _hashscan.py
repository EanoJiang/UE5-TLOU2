import json,pathlib,struct,collections
cap=json.loads(pathlib.Path('Exports/ExactDebug/ellie16_patrol_body/capture.json').read_text()); by={int(x.get('hash',x.get('bone_hash','0')),0) if isinstance(x.get('hash',x.get('bone_hash','0')),str) else x.get('hash',0):x for x in cap['bones']}
# inspect structures with hashes values maybe cap fields
print(cap['bones'][0]);
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes(); regions=[('codec',0x95ae20,2496),('anim',0x9d5070,4096),('raw',0x9a77f0,0x500)]
# robust hash list from common keys
hs=set()
for x in cap['bones']:
 for k in ['hash','bone_hash','name_hash']:
  v=x.get(k)
  if isinstance(v,int): hs.add(v)
  elif isinstance(v,str) and v.startswith('0x'):
   try:hs.add(int(v,16))
   except:pass
print('hashes',len(hs))
for nm,q,n in regions:
 hits=[]
 for o in range(0,n-8):
  v=struct.unpack_from('<Q',b,q+o)[0]
  if v in hs:hits.append((o,v))
 print(nm,'hits',len(hits),[(hex(o),hex(v)) for o,v in hits[:20]])
