import json,pathlib
D=json.loads(pathlib.Path('Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json').read_text())
for r in D['channels']:
 if r['anim_name']=='ellie-prone-lg-aim-strafe-0-fw': print(r)
