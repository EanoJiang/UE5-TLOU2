import json,collections
m=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\DecodedRawChannels\rawchannels_decode_manifest.json')); a=[]
for s in m['sources']:
 for r in s.get('records',[]):
  a.append((r['channel_count'],s['name'],r['page'],r['entry'],r['resource_offset'],r['resource_size']))
for x in sorted(a,reverse=True)[:100]:print(x)
