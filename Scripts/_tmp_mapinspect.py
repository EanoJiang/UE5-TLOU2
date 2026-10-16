import json,glob,math
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\static_transform_candidates.json'
rows=json.load(open(p)); print('rows',len(rows));
for x in rows[:20]: print(x['source'],x['resource_offset'],x['channel_index'],x['hash'],x['transform'])
d=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json')); print('bones',len(d['bones']))
for x in d['bones'][:10]: print(x['index'],x['name'],x['parentIndex'],x['matrix'])
