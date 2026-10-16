import json,pathlib
D=json.loads(pathlib.Path('Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json').read_text())
# parser only clips/channels, rebuild list maybe analyze raw source script parse? use analyze_anim_structure output command modified? just inspect page9 names clips around index entries
for c in D['clips']:
 if c['page']==9 and 430<=c['anim_entry']<=500: print(c['anim_entry'],c['anim_name'],c['raw_entry'],c['codec']['rel'] if c['codec'] else None)
