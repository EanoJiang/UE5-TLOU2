"""Compare UE-evaluated local SQT against all native-decoded 0FW keys."""
import json,math
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
src=json.load(open(ROOT/'Exports/AnimationSources/DecodedOriginal/ellie-prone-lg-aim-strafe-0-fw.json'))
ue=json.load(open(ROOT/'Exports/original_0fw_ue_poses.json'))
rows=[]
for t in src['tracks']:
    eT=[t['translation'][0],t['translation'][2],t['translation'][1]]
    maxT=maxQ=maxS=0.
    for f in ue['frames']:
        k=f['frame'];got=f['bones'][t['bone_name']];q=t['rotations_xyzw'][k]
        # Export FBX -Z forward/Y up -> UE left-handed Z up. At the bone-local
        # boundary this is P(x,y,z)=(x,z,y), a reflection. Quaternion vector
        # components transform by det(P)*P and W is unchanged.
        eQ=[-q[0],-q[2],-q[1],q[3]]
        maxT=max(maxT,max(abs(a-b) for a,b in zip(eT,got['translation'])))
        maxQ=max(maxQ,min(max(abs(a-b) for a,b in zip(eQ,got['rotation_xyzw'])),max(abs(a+b) for a,b in zip(eQ,got['rotation_xyzw']))))
        maxS=max(maxS,max(abs(a-b) for a,b in zip(t['scale'],got['scale'])))
    rows.append({'bone':t['bone_name'],'bone_index':t['bone_index'],'frames':len(ue['frames']),'max_translation_error_m':maxT,'max_quaternion_component_error':maxQ,'max_scale_error':maxS})
out={'source':src['source'],'asset':ue['asset'],'frames':len(ue['frames']),'driven_bones':len(rows),'max_translation_error_m':max(r['max_translation_error_m'] for r in rows),'max_quaternion_component_error':max(r['max_quaternion_component_error'] for r in rows),'max_scale_error':max(r['max_scale_error'] for r in rows),'all_poses_valid':all(f['valid'] for f in ue['frames']),'rows':rows,'units_note':'UE bone-local SQT remains meters under a synthetic root scale100; world result is UE centimeters.'}
out['pass']=out['frames']==80 and out['driven_bones']==26 and out['all_poses_valid'] and out['max_translation_error_m']<1e-4 and out['max_quaternion_component_error']<1e-4 and out['max_scale_error']<1e-4
json.dump(out,open(ROOT/'Exports/original_0fw_ue_transform_validation.json','w'),indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ('rows','source')},indent=2))
if not out['pass']:raise RuntimeError('original0FW UE local SQT mismatch')
