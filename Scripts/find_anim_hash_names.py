import json, re, os
targets=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
def fnv1a(s):
 h=0xcbf29ce484222325
 for c in s.encode(): h=((h^c)*0x100000001b3)&0xffffffffffffffff
 return h
names=[]
for p in [r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json']:
 if os.path.isfile(p):
  d=json.load(open(p)); names += [x['name'] for x in d.get('bones',[])]
print('bone_names',len(names))
for t in targets:
 hits=[n for n in names if fnv1a(n)==t or fnv1a(n.lower())==t or fnv1a(n.upper())==t]
 print(hex(t),hits)
for s in ['ANIM_RAWCHANNELS','ANIM','ANIM_GROUP']:
 print(s,hex(fnv1a(s)))
