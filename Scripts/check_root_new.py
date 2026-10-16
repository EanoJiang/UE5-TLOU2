import json
x=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_trajectory_evidence.json'))
for f in sorted(set(t['format'] for t in x['tracks'])):
 ts=[t for t in x['tracks'] if t['format']==f]; print(f,[(t['page'],t['entry'],t['sample_count'],t['encoded_frame_count'],t['stored_row_count'],len(t['extra_rows']),len(t['tail'])) for t in ts])
