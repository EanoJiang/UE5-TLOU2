import re,struct,json,collections
T=set(int(x['hash'],16) for x in json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json'))['sources'][1]['records'][0]['channels'])
# collect all unique channel hashes globally
M=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json'));T=set()
for s in M['sources']:
 for r in s.get('records',[]):
  for c in r.get('channels',[]):T.add(int(c['hash'],16))

def f(d,seed=0xcbf29ce484222325):
 h=seed
 for x in d:h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
for p in [r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak',r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak']:
 b=open(p,'rb').read(); print('FILE',p,'size',len(b)); strings=[];o=0
 # all ascii strings >=2
 for m in re.finditer(rb'[\x20-\x7e]{2,}',b):
  x=m.group().decode('ascii','ignore'); strings.append((m.start(),x))
 print('strings',len(strings))
 for off,x in strings:
  for y in [x,x.lower(),x.upper(),x+'\0',x.lower()+'\0']:
   for enc in ['utf-8','utf-16-le']:
    h=f(y.encode(enc))
    if h in T:print('HIT',hex(h),repr(x),'var',repr(y),'enc',enc,'off',off)
 # combos common suffixes/prefixes using all strings not too large
 print('target count',len(T))
