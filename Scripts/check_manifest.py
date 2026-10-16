import json
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\animation_source_manifest.json'; d=json.load(open(p)); print('sources',len(d['sources']));
for s in d['sources']: print(s['source'], 'chunks',len(s.get('chunks',[])), 'err',s.get('error'))
print('invalid',sum(1 for s in d['sources'] for c in s.get('chunks',[]) if not c.get('valid')))
