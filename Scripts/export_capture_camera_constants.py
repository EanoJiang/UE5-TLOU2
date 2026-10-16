"""Export the coherent original viewer camera from a bound view-general CBV."""
from pathlib import Path
import json
import math
import numpy as np
from ngfx_resource_reader import read_resource, object_blob

ROOT = Path('D:/TLOU2_UE5_8_Codex')
CAP = ROOT / 'Exports/CaptureBuffers'
REPORT = ROOT / 'Content/TLOU2/Reports'


def main():
    address = 695238991104
    gpu_base = int.from_bytes(object_blob(7556, 'create')[104:112], 'little')
    assert gpu_base == 0xa1d9800000
    offset = address - gpu_base
    values = np.frombuffer(read_resource(7556, offset, 2864), '<f4')
    view = values[:16].reshape(4, 4).astype(float)
    vp = values[16:32].reshape(4, 4).astype(float)
    previous_vp = values[32:48].reshape(4, 4).astype(float)
    projection = vp @ np.linalg.inv(view)
    inverse = np.linalg.inv(view)
    camera = inverse[:3, 3]
    forward = inverse[:3, 2]
    explicit_camera = values[48:51].astype(float)
    C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
    h_fov = math.degrees(2 * math.atan(1 / abs(projection[0, 0])))
    v_fov = math.degrees(2 * math.atan(1 / abs(projection[1, 1])))
    orth_error = float(np.max(np.abs(view[:3, :3] @ view[:3, :3].T - np.eye(3))))
    position_error = float(np.max(np.abs(camera - explicit_camera)))
    ratio = abs(projection[1, 1] / projection[0, 0])
    assert orth_error < 1e-6 and position_error < 1e-6
    assert abs(ratio - 1920 / 1080) < 1e-6
    bindings = json.loads((CAP / 'graphics_descriptor_bindings_probe.json').read_text())
    draws = []
    for draw in bindings['dispatches']:
        slots = draw.get('tables', {}).get('3', {}).get('slots', [])
        if len(slots) >= 4 and slots[3] and slots[3].get('address') == address:
            draws.append({k: draw[k] for k in ('sequence', 'commandlist_uid', 'command_index', 'pipeline_uid', 'draw_args')})
    assert draws
    report = {
        'pass': True, 'resource_uid': 7556, 'resource_gpu_base': gpu_base,
        'view_cbv_gpu_address': address, 'view_cbv_resource_offset': offset,
        'view_cbv_logical_bytes': 2864, 'view_cbv_allocated_bytes': 3072,
        'root_signature_uid': 10602, 'root_signature_chunk': 47387,
        'graphics_root_parameter': 3, 'descriptor_table_slot': 3,
        'shader_binding': 'cb3,space2; hostlayout.g_view_general',
        'shader_evidence': str(CAP / 'Shaders/chunk_47400.asm.txt'),
        'view_game': view.tolist(), 'view_projection_game': vp.tolist(),
        'previous_view_projection_game': previous_vp.tolist(), 'projection_derived': projection.tolist(),
        'camera_position_game_meters_y_up': camera.tolist(),
        'explicit_camera_position_game_meters_y_up': explicit_camera.tolist(),
        'camera_forward_game': forward.tolist(),
        'camera_position_blender_meters_z_up': (C @ camera).tolist(),
        'camera_forward_blender': (C @ forward).tolist(),
        'horizontal_fov_degrees': h_fov, 'vertical_fov_degrees': v_fov,
        'downward_pitch_degrees': math.degrees(math.asin(-forward[1])),
        'sensor36mm_equivalent_horizontal_lens_mm': 18 * abs(projection[0, 0]),
        'projection_aspect_ratio': ratio,
        'near_clip_meters': -projection[2, 3] / projection[2, 2],
        'far_clip_meters': -projection[2, 3] / (projection[2, 2] - 1),
        'projection_taa_jitter_xy': [projection[0, 2], projection[1, 2]],
        'validation': {'view_rotation_orthonormal_max_error': orth_error,
                       'inverse_view_vs_explicit_camera_max_error_meters': position_error,
                       'aspect_vs1920x1080_error': abs(ratio - 1920 / 1080)},
        'actual_indexed_draw_bindings': draws,
        'scope': 'Camera values are original captured initial bytes from a coherent view-general CBV also bound in actual indexed draws. A later frame uses a different view-CBV address whose initial bytes are stale/incoherent; those are not substituted. View/VP order and projection are validated by matrix algebra and explicit camera-position agreement. Root signature10602 is independently linked to pipeline13601, whose vertex shader47400 declares cb3,space2 as g_view_general.',
        'placement_note': 'These coordinates include the original actor-world calibration. If the exported captured pose removes actor-world W, transform camera position and forward by inverse(W), or restore W to the actor before using the original camera. Blender basis C: game(x,y,z) -> Blender(x,-z,y).'}
    palette_path = CAP / 'Ellie_Capture_SkinPalette1038.npz'
    if palette_path.exists():
        palette = np.load(palette_path)
        actor_world = palette['actor_world_game'].astype(float)
        inverse_actor = np.linalg.inv(actor_world)
        local_camera = (inverse_actor @ np.r_[camera, 1])[:3]
        local_forward = (inverse_actor @ np.r_[forward, 0])[:3]
        report.update(actor_world_source=str(palette_path), actor_world_game=actor_world.tolist(),
                      camera_position_actor_local_game_meters=local_camera.tolist(),
                      camera_forward_actor_local_game=local_forward.tolist(),
                      camera_position_actor_local_blender_meters=(C @ local_camera).tolist(),
                      camera_forward_actor_local_blender=(C @ local_forward).tolist())
    path = REPORT / 'CAPTURE_ORIGINAL_CAMERA_CONSTANTS.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    text = f'''# Captured original gallery camera

Original bound view-general CBV: GPU0xa1df791d00, UID7556 byte offset{offset}, logical2864B, allocated3072B. Graphics root3 table slot3 maps cb3,space2. Root signature10602/chunk47387 and original vertex shader47400 independently confirm this layout.

- Game coordinates, meters/Y-up: camera{camera.tolist()}, forward{forward.tolist()}.
- Blender coordinates, meters/Z-up: camera{(C @ camera).tolist()}, forward{(C @ forward).tolist()}.
- Horizontal FOV{h_fov:.8f} degrees; vertical FOV{v_fov:.8f} degrees; downward pitch{report['downward_pitch_degrees']:.8f} degrees.
- Horizontal36mm-sensor lens equivalent{report['sensor36mm_equivalent_horizontal_lens_mm']:.8f}mm. Aspect{ratio:.10f} matches1920x1080.
- Near clip{report['near_clip_meters']:.8f}m. Projection contains the original small TAA jitter; a stable recreation may omit it.

Inverse-view camera position agrees with the explicit CBV camera float4 within{position_error:.3g}m. View rotation orthonormal error{orth_error:.3g}. The report retains the exact view, VP, previous VP, derived projection and{len(draws)} actual indexed-draw bindings.

{report['placement_note']}

For the export with actor-world W removed, camera Blender position is{report.get('camera_position_actor_local_blender_meters')}m and forward is{report.get('camera_forward_actor_local_blender')}. These values apply inverse(W) from the validated captured human-palette export.

{report['scope']}
'''
    (REPORT / 'CAPTURE_ORIGINAL_CAMERA_CONSTANTS.md').write_text(text, encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('pass', 'view_cbv_resource_offset', 'camera_position_game_meters_y_up', 'horizontal_fov_degrees', 'vertical_fov_degrees', 'downward_pitch_degrees', 'validation')}, indent=2))
    print('ACTUAL_INDEXED_DRAW_BINDINGS', len(draws))


if __name__ == '__main__':
    main()
