import json
m=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json'))
for s in m['sources']:
 for r in s.get('records',[]):
  if s['name']=='anim-ellie-player-movement.pak' and r['page']==9 and 600000<r['resource_offset']%1000000<620000:
   print('rec',r['entry'],'offset',r['resource_offset'],'size',r['resource_size'],'count',r['channel_count'],'hashes',[c['hash'] for c in r['channels']])
