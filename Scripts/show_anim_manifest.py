import json
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\animation_source_manifest.json'; d=json.load(open(p));
for s in d['sources']:
 print('\n',s['source'])
 for c in s.get('chunks',[]):
  if c.get('valid'):
   print('chunk',c['chunk'],'resources',[(r['name'],r['type'],r['absolute_offset']) for r in c['resources'][:15]])
   print('codec',c['codec'])
