import json
m=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json'))
for s in m['sources']:
 for r in s.get('records',[]):
  if s['name']=='anim-ellie-player-movement.pak' and r['resource_offset'] in [10123248,10121648,10120048]:
   print('REC',r['page'],r['entry'],r['resource_offset'],r['resource_size'],r['channel_count'])
   for c in r['channels']:print(c)
