"""Export original FG turntable vertices posed by the captured16 skin palette."""
from pathlib import Path
import json
import hashlib
import numpy as np
from ngfx_resource_reader import read_resource
from verify_capture_mesh_skin_sources import source_skin, captured_skin

ROOT = Path('D:/TLOU2_UE5_8_Codex')
RAW = ROOT / 'Exports/ExactDebug/keyart_turntable_fg'
OUT = ROOT / 'Exports/CapturedFGStage'
REPORT = ROOT / 'Content/TLOU2/Reports'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = json.loads((RAW / 'capture.json').read_text())
    assert raw['boneCount'] == 16 and len(raw['meshes']) == 33
    palette_offset = 125370368
    palette_bytes = read_resource(7556, palette_offset, 16 * 48)
    skin = np.frombuffer(palette_bytes, '<f4').reshape(16, 3, 4).copy()
    C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype='<f4')
    binding = json.loads((ROOT / 'Exports/CaptureBuffers/deformer_descriptor_bindings_probe.json').read_text())
    dispatches = []
    cache = {}
    for command in binding['dispatches']:
        if command['pipeline_uid'] not in (7931, 7932, 7939):
            continue
        cbv, vertex, weight = command['tables']['3']['slots'][:3]
        key = vertex['resource_uid'], vertex['first_element'], weight['first_element'], command['pipeline_uid']
        if key not in cache:
            cache[key] = captured_skin(vertex, weight, command['pipeline_uid'])
        dispatches.append({**cache[key], 'sequence': command['sequence'], 'command_index': command['command_index'],
                           'pipeline_uid': command['pipeline_uid'], 'deformer_cbv_gpu_address': cbv['address']})
    rows = []
    for number, mesh in enumerate(raw['meshes']):
        digest, nonzero, encoding = source_skin(RAW, mesh)
        assert encoding == 'packed22weight10joint'
        exact = [d for d in dispatches if d['vertices'] == mesh['vertex_count'] and d['skin_sha256'] == digest]
        assert exact, ('not bound source skin', mesh['name'])
        z = np.load(RAW / mesh['npz'])
        n = mesh['vertex_count']
        positions = z['pos_raw'].view('<f4').reshape(n, mesh['bindings']['pos']['stride'] // 4)[:, :3].copy()
        ids = z['bidx_raw'].view('<u2').reshape(n, 12).astype('<u4')
        packed_weights = z['bwgt_raw'].view('<u4').reshape(n, 12)
        weights = packed_weights.astype('<f4') * np.array(0x34800002, dtype='<u4').view('<f4')
        posed = np.zeros((n, 3), dtype='<f4')
        p4 = np.concatenate((positions, np.ones((n, 1), dtype='<f4')), axis=1)
        for influence in range(12):
            matrices = skin[ids[:, influence]]
            contribution = np.einsum('nij,nj->ni', matrices, p4, optimize=False)
            posed += contribution * weights[:, influence, None]
        bone_ids = np.unique(ids[packed_weights > 0]).tolist()
        arrays = {key: z[key] for key in z.files}
        arrays.update(positions_game_meters=positions, posed_positions_game_meters=posed,
                      posed_positions_blender_meters=posed @ C.T,
                      original_joint_ids=ids, original_packed_weight22=packed_weights,
                      shader_weights_float32=weights, captured_skin_matrices_game=skin)
        name = f'mesh_{number:04d}.npz'
        np.savez_compressed(OUT / name, **arrays)
        row = {**mesh, 'source_npz': str(RAW / mesh['npz']), 'posed_npz': str(OUT / name),
               'source_bone_ids': bone_ids, 'source_bone_names': [raw['bones'][b]['name'] for b in bone_ids],
               'source_skin_sha256': digest, 'actual_dispatch_matches': exact,
               'source_bounds_game_meters': [positions.min(axis=0).tolist(), positions.max(axis=0).tolist()],
               'posed_bounds_game_meters': [posed.min(axis=0).tolist(), posed.max(axis=0).tolist()],
               'source_weight_sum_max_error': float(np.max(np.abs(weights.sum(axis=1) - 1))),
               'visible_variant_note': 'Expanded concrete variant' if bone_ids == [5] else
                                       'Other variants retained at captured smaller positions; may be occluded by concrete surface'}
        rows.append(row)
    cross_checks = []
    for offset in (5832704, 12124160, 121176064, 131661824, 133758976):
        other = np.frombuffer(read_resource(7556, offset, 16 * 48), '<f4').reshape(16, 3, 4)
        cross_checks.append({'resource_offset': offset, 'max_abs_matrix_error': float(np.max(np.abs(other - skin)))})
    report = {'source_pak': 'keyart-turntable-fg.pak', 'source_metadata': str(RAW / 'capture.json'),
              'meshes': 33, 'vertices': sum(r['vertex_count'] for r in rows), 'bit_exact_bound_source_skin_subsets': 33,
              'palette_resource_uid': 7556, 'palette_resource_offset': palette_offset,
              'palette_sha256': hashlib.sha256(palette_bytes).hexdigest(),
              'matrix_layout': '16 consecutive float32 affine3x4 matrices, three float4 rows per bone; game meters Y-up',
              'basis_game_to_blender': 'x,y,z -> x,-z,y',
              'palette': [{'bone_index': i, 'bone_name': b['name'], 'parent_index': b['parentIndex'],
                           'skin_matrix_game': skin[i].tolist()} for i, b in enumerate(raw['bones'])],
              'repeated_palette_cross_checks': cross_checks,
              'instance_world_status': 'Actual graphics instance transform is being recovered separately; do not apply the old empirical .61 stage scale to these posed vertices.',
              'pose_method': 'Original packed22/10 influences, original shader float32 multiplier bits0x34800002; no weight normalization. Float32 CPU LBS, original palette and original per-vertex influence order. Vertex output is a portable evaluation, not a GPU readback.',
              'source_selection_evidence': 'Every FG33 subset has exact original skin-record bytes in actual captured compute dispatches. Wet-large and separate concrete-large moss subsets do not match current dispatch vertex counts. Captured concrete bone5 expands the FG concrete group from~.24m radius to~.8m and raises its ground from~-0.1m to~0m.',
              'rows': rows}
    (OUT / 'captured_fg_stage_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (REPORT / 'CAPTURE_FG_STAGE_VALIDATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('meshes', 'vertices', 'bit_exact_bound_source_skin_subsets', 'palette_resource_offset', 'repeated_palette_cross_checks')}, indent=2))
    print('CONCRETE_GROUP', [(r['name'], r['vertex_count'], r['posed_bounds_game_meters']) for r in rows if r['source_bone_ids'] == [5]])


if __name__ == '__main__':
    main()
