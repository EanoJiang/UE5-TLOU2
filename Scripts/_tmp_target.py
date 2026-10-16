import json,struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json';m=json.load(open(p));
for s in m['sources']:
 for r in s.get('records',[]):
  if s['name']=='anim-ellie-player-movement.pak' and (r['page']==9 and r['entry'] in list(range(210,225)) or r['resource_offset'] in [10151552]):
   print('REC',r['page'],r['entry'],'offset',r['resource_offset'],'size',r['resource_size'],'count',r['channel_count'])
   for c in r['channels']:
    print(c['index'],c['hash'],c.get('format'),c.get('payload_bytes'),c.get('descriptor_ptr'),c.get('data_ptr'),c.get('dynamic_half_count'))
