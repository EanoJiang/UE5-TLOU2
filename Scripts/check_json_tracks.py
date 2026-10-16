import json
x=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_trajectory_evidence.json'))
for t in x['tracks']:
 if t['format'] in ('0x00fb0050','0x00fb005f','0x00fb0088','0x00fb0105'):
  print(t['page'],t['entry'],t['format'],t['sample_count'],len(t['samples']),t['samples'][-5:],t['tail'])
