"""Independent source S/Q/T comparison for the UE two-sample static hold.

Both imported samples must equal the one original source pose. A two-sample
carrier is an interchange workaround, not an invented source animation.
"""
import json
from pathlib import Path

ROOT = Path('D:/TLOU2_UE5_8_Codex')
src = json.loads((ROOT/'Exports/AnimationSources/DecodedOriginal/model-viewer-ellie-16-patrol.json').read_text())
ue = json.loads((ROOT/'Exports/original_viewer_ue_poses.json').read_text())
rows = []
for track in src['tracks']:
    q = track['rotations_xyzw'][0]
    t = track['translation']
    s = track['scale']
    expected_t = [t[0], t[2], t[1]]
    expected_q = [-q[0], -q[2], -q[1], q[3]]
    expected_s = [s[0], s[2], s[1]]
    max_t = max_q = max_s = 0.0
    for frame in ue['frames']:
        actual = frame['bones'][track['bone_name']]
        max_t = max(max_t, max(abs(a-b) for a,b in zip(expected_t, actual['translation'])))
        max_q = max(max_q, min(max(abs(a-b) for a,b in zip(expected_q, actual['rotation_xyzw'])),
                               max(abs(a+b) for a,b in zip(expected_q, actual['rotation_xyzw']))))
        max_s = max(max_s, max(abs(a-b) for a,b in zip(expected_s, actual['scale'])))
    rows.append({'bone': track['bone_name'], 'bone_index': track['bone_index'],
                 'max_translation_error_m': max_t, 'max_quaternion_component_error': max_q,
                 'max_scale_error': max_s})
out = {'source': str(ROOT/'Exports/AnimationSources/DecodedOriginal/model-viewer-ellie-16-patrol.json'),
       'asset': ue['asset'], 'source_frames': src['frame_count'], 'ue_carrier_samples': len(ue['frames']),
       'driven_bones': len(rows), 'all_poses_valid': all(f['valid'] for f in ue['frames']),
       'max_translation_error_m': max(r['max_translation_error_m'] for r in rows),
       'max_quaternion_component_error': max(r['max_quaternion_component_error'] for r in rows),
       'max_scale_error': max(r['max_scale_error'] for r in rows), 'rows': rows,
       'units_note': 'UE bone-local SQT remains meters under a synthetic root scale100; world result is UE centimeters.',
       'hold_note': 'Two identical UE samples reproduce one original catalog pose; source displacement is zero.'}
out['pass'] = (out['source_frames'] == 1 and out['ue_carrier_samples'] == 2 and out['driven_bones'] == 520
               and out['all_poses_valid'] and out['max_translation_error_m'] < 1e-4
               and out['max_quaternion_component_error'] < 1e-4 and out['max_scale_error'] < 1e-4)
(ROOT/'Exports/original_viewer_ue_transform_validation.json').write_text(json.dumps(out, indent=2))
print(json.dumps({k:v for k,v in out.items() if k != 'rows'}, indent=2))
if not out['pass']:
    raise RuntimeError('Original Ellie16 viewer pose differs from imported UE local transforms')
