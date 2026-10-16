import sys,struct,json,collections;sys.path.insert(0,'Scripts');import decode_root_candidate_tracks as d
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read(); doc=d.parse(p); vals=[]
for c in doc['codec_rate_evidence']:
 vals.append((round(c['sample_rate_hz'],6),round(c['sample_period_s'],9)))
print('codec rate pairs',collections.Counter(vals))
