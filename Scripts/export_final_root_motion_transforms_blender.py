"""Read-only Root Motion transform audit of the final three animated Blender files."""
import bpy
import csv
import hashlib
import json
from pathlib import Path
from mathutils import Matrix

ROOT = Path('D:/TLOU2_UE5_8_Codex')
C = Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
STEMS = ['Ellie_Patrol_CapturedSkinPose', 'Ellie16_Patrol_OriginalViewerPose', 'Ellie_Patrol_Original_0FW']
files = []
for stem in STEMS:
    source = ROOT/'Blender'/(stem+'.blend')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    count = 80 if stem.endswith('_0FW') else 1
    rate = 30.
    rows = []
    first = None
    max_translation = max_rotation = max_matrix = 0.
    for frame in range(count):
        bpy.context.scene.frame_set(frame+1)
        bpy.context.view_layer.update()
        transform = C.transposed() @ arm.matrix_world @ arm.pose.bones['root'].matrix @ C
        if first is None:
            first = transform.copy()
        delta = first.inverted() @ transform
        translation, rotation, scale = transform.decompose()
        delta_t, delta_r, delta_s = delta.decompose()
        max_translation = max(max_translation, (translation-first.translation).length)
        max_rotation = max(max_rotation, abs(delta_r.angle))
        max_matrix = max(max_matrix, max(abs(delta[i][j]-(1. if i == j else 0.)) for i in range(4) for j in range(4)))
        row = {'frame': frame, 'time_s': frame/rate,
               'root_x_m': translation.x, 'root_y_m': translation.y, 'root_z_m': translation.z,
               'root_qx': rotation.x, 'root_qy': rotation.y, 'root_qz': rotation.z, 'root_qw': rotation.w,
               'root_sx': scale.x, 'root_sy': scale.y, 'root_sz': scale.z,
               'delta_x_m': delta_t.x, 'delta_y_m': delta_t.y, 'delta_z_m': delta_t.z,
               'delta_qx': delta_r.x, 'delta_qy': delta_r.y, 'delta_qz': delta_r.z, 'delta_qw': delta_r.w}
        rows.append(row)
    destination = ROOT/'Exports'/(stem+'_RootMotion_GameSpace.csv')
    with destination.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    # Float32 inverse/multiply can leave a small identity residual despite a
    # perfectly unchanged source pose; displacement/rotation are the direct tests.
    passed = max_translation < 1e-10 and max_rotation < 1e-6 and max_matrix < 2e-6
    files.append({'source_blend': str(source), 'source_blend_sha256': digest,
                  'csv': str(destination), 'csv_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                  'frames': count, 'sample_rate_hz': rate, 'bone': 'root',
                  'maximum_root_position_displacement_m': max_translation,
                  'maximum_delta_rotation_radians': max_rotation,
                  'maximum_delta_identity_matrix_component_error': max_matrix, 'pass': passed})
report = {'pass': all(row['pass'] for row in files), 'files': files,
          'coordinate_convention': 'Original game actor-local basis: X right, Y up, Z forward; meters; quaternion XYZW. Full transform first^-1*current yields deltas. Existing *_RootTrajectory.csv files use Blender X right/Y backward/Z up and remain available with their original values.',
          'root_policy': 'The original named root is elevated near the pelvis. Its reference position is not travel. All source samples have zero root displacement and rotation. UE introduces an armature object root for basis/centimeter conversion; that root is also stationary. No locomotion or synthetic Root Motion is inferred.',
          'scope': 'Evaluated delivered rig root transforms, not reconstruction of absent full-body animation or procedural motion.'}
(ROOT/'Exports/final_root_motion_transform_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('FINAL_ROOT_MOTION_TRANSFORMS '+json.dumps(report))
assert report['pass']
