import json,collections
m=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedSkelRaw2\rawchannels_decode_manifest.json')); print('resources',len(m['sources'][0]['records']))
for r in m['sources'][0]['records']:
 print(r['page'],r['entry'],r['resource_offset'],r['channel_count'])
 for c in r['channels']:
  print(' ',c['index'],c['hash'],c.get('format'),c.get('payload_bytes'),c.get('baseline_transform_fields',{}).get('translation') if c.get('baseline_transform_fields') else None)
