"""Independently compare every source SQT sample with actual canonical GLB bytes."""
import hashlib
import json
from pathlib import Path

import numpy as np
from verify_exported_gltf_pose_independent import accessor, load_glb, node_matrix

ROOT = Path(__file__).resolve().parents[1]
C = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)
CLIPS = [
    ('Ellie_Patrol_Original_0FW', 'ellie-prone-lg-aim-strafe-0-fw'),
    ('Ellie16_Patrol_OriginalViewerPose', 'model-viewer-ellie-16-patrol'),
]


def sample(times, values, time, rotation=False, interpolation='LINEAR'):
    nearest = int(np.argmin(np.abs(times-time)))
    if abs(times[nearest]-time) < 1e-6:
        return values[nearest].astype(float)
    if time <= times[0]:
        return values[0].astype(float)
    if time >= times[-1]:
        return values[-1].astype(float)
    right = int(np.searchsorted(times, time))
    left = right-1
    a, b = values[left].astype(float), values[right].astype(float)
    if interpolation == 'STEP':
        return a
    assert interpolation == 'LINEAR', interpolation
    f = (time-times[left])/(times[right]-times[left])
    if not rotation:
        return a+(b-a)*f
    a /= np.linalg.norm(a)
    b /= np.linalg.norm(b)
    dot = float(a@b)
    if dot < 0:
        b, dot = -b, -dot
    if dot > .9995:
        q = a+(b-a)*f
        return q/np.linalg.norm(q)
    angle = np.arccos(np.clip(dot, -1, 1))
    return (np.sin((1-f)*angle)*a+np.sin(f*angle)*b)/np.sin(angle)


def verify(stem, clip):
    path = ROOT/'Exports'/(stem+'.glb')
    source_path = ROOT/'Exports/AnimationSources/DecodedOriginal'/(clip+'.json')
    source = json.loads(source_path.read_text())
    raw, doc, binary = load_glb(path)
    assert len(doc['animations']) == 1
    animation = doc['animations'][0]
    nodes = {n['name']: i for i, n in enumerate(doc['nodes']) if 'name' in n}
    channels = {}
    for channel in animation['channels']:
        sampler = animation['samplers'][channel['sampler']]
        key = (channel['target']['node'], channel['target']['path'])
        assert key not in channels
        channels[key] = (accessor(doc, binary, sampler['input']).ravel().astype(float),
                         accessor(doc, binary, sampler['output']), sampler.get('interpolation', 'LINEAR'))
    count = int(source['frame_count'])
    rate = float(source.get('sample_rate_hz') or 30)

    def evaluate(index, time):
        node = dict(doc['nodes'][index])
        for prop in ('translation', 'rotation', 'scale'):
            if (index, prop) in channels:
                times, values, interpolation = channels[index, prop]
                node.pop('matrix', None)
                node[prop] = sample(times, values, time, prop == 'rotation', interpolation).tolist()
        return node_matrix(node)

    rows = []
    for track in source['tracks']:
        index = nodes[track['bone_name']]
        translation_error = matrix_error = 0.
        for frame in range(count):
            quaternion = np.array(track['rotations_xyzw'][frame], dtype=float)
            quaternion /= np.linalg.norm(quaternion)
            expected = C@node_matrix({'translation': track['translation'], 'rotation': quaternion,
                                      'scale': track['scale']})@C.T
            # glTF cancels the external Blender basis at the armature boundary.
            # Child joints retain the converted local basis; root has no bone parent.
            if track['bone_name'] == 'root':
                expected = C.T@expected
            actual = evaluate(index, (frame+1)/rate)
            translation_error = max(translation_error, float(np.max(np.abs(actual[:3, 3]-expected[:3, 3]))))
            matrix_error = max(matrix_error, float(np.max(np.abs(actual-expected))))
        rows.append({'bone': track['bone_name'], 'samples': count,
                     'maximum_translation_component_error_m': translation_error,
                     'maximum_local_sqt_matrix_component_error': matrix_error})
    root_index = nodes['root']
    root_positions = np.array([evaluate(root_index, (frame+1)/rate)[:3, 3] for frame in range(count)])
    root_displacement = float(np.max(np.linalg.norm(root_positions-root_positions[0], axis=1)))
    result = {'glb': str(path), 'glb_sha256': hashlib.sha256(raw).hexdigest(),
              'source': str(source_path), 'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'animation': animation['name'], 'frames': count, 'sample_rate_hz': rate, 'driven_bones': len(rows),
              'maximum_translation_component_error_m': max(r['maximum_translation_component_error_m'] for r in rows),
              'maximum_local_sqt_matrix_component_error': max(r['maximum_local_sqt_matrix_component_error'] for r in rows),
              'root_local_translation_displacement_m': root_displacement,
              'method': 'Parse GLB accessors and animation samplers independently of Blender; evaluate all original source frame times and compare source normalized-quaternion SQT. Child joints use C*source*C^T; the armature boundary cancels left C for the root. Root displacement checks source root local translation; no new trajectory is introduced.',
              'scope': 'All driven bone local SQT samples. Does not assert original full-body locomotion, unrecorded helper transforms or dynamic cloth simulation.',
              'tolerance_matrix_component': 2e-5, 'rows': rows}
    result['pass'] = result['maximum_local_sqt_matrix_component_error'] < 2e-5 and root_displacement < 1e-10
    assert result['pass'], {k: v for k, v in result.items() if k != 'rows'}
    return result


results = [verify(*clip) for clip in CLIPS]
out = {'pass': all(r['pass'] for r in results), 'clips': results}
destination = ROOT/'Exports/original_animation_glb_sample_validation.json'
destination.write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps({'pass': out['pass'], 'clips': [{k: v for k, v in r.items() if k != 'rows'} for r in results]}, indent=2))
