import json,math,collections
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_trajectory_evidence.json';d=json.load(open(p));
for fmt in sorted(set(t['format'] for t in d['tracks'])):
 ts=[t for t in d['tracks'] if t['format']==fmt]; ar=ts[0]['arity']; vals=[v for t in ts for row in t['samples'] for v in row]; print(fmt,'tracks',len(ts),'N',sorted(set(t['sample_count'] for t in ts)),'ranges',min(vals),max(vals),'first',ts[0]['samples'][:3],'last',ts[0]['samples'][-3:])
