import json, pathlib, collections
p=pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json')
d=json.loads(p.read_text())
for c in d['clips'][:20]: print(c['page'],c['anim_entry'],c['anim_name'],c['codec'])
t=[c for c in d['clips'] if c['anim_name']=='ellie-prone-lg-aim-strafe-0-fw'][0];print('TARGET',t)
# group same groups/frames/stride/header payload
for c in d['clips']:
 h=c['codec'] or {}
 if h.get('groups')==7 and h.get('frames') in range(75,100):
  print(c['anim_name'],h.get('frames'),h.get('payload_size'),h.get('rel'), c['raw_count'],hex(h.get('offset',0)))
