import json,struct,collections,os
# Build bone hash dict using known FNV1a lower? Names exact
def fnv(s):
 h=0xcbf29ce484222325
 for x in s.encode(): h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
byhash={fnv(x['name']):(x['index'],x['name']) for x in D['bones']}
M=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json'))
counts=collections.Counter(); recs={}
for src in M['sources']:
 for r in src.get('records',[]):
  for c in r.get('channels',[]):
   h=int(c['hash'],16); counts[h]+=1; recs.setdefault(h,[]).append((src['name'],r['page'],r['entry'],c.get('format'),c.get('payload_bytes')))
print('unique',len(counts),'bonehits',sum(h in byhash for h in counts))
for h,n in sorted(counts.items(), key=lambda x:(x[0])):
 print(f'0x{h:016x}',n,byhash.get(h,''),recs[h][:2])
