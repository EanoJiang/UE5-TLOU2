"""Add separately named world-posed FG NPZ files without replacing skin-only NPZs."""
from pathlib import Path
import json
import math
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/CapturedFGStage'
REPORT = ROOT / 'Content/TLOU2/Reports'


def main():
    doc = json.loads((OUT / 'captured_fg_stage_manifest.json').read_text())
    instance = json.loads((REPORT / 'CAPTURE_FG_STAGE_INDEX_INSTANCE_VALIDATION.json').read_text())
    world = np.asarray(instance['instance_world_matrix_game'], dtype='<f4')
    C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype='<f4')
    draws = json.loads((ROOT / 'Exports/CaptureBuffers/fg_stage_index_draw_matches.json').read_text())
    for i, row in enumerate(doc['rows']):
        original = np.load(row['posed_npz'])
        arrays = {k: original[k] for k in original.files}
        posed = arrays['posed_positions_game_meters']
        world_pos = posed @ world[:3, :3].T + world[:3, 3]
        arrays.update(posed_world_positions_game_meters=world_pos,
                      posed_world_positions_blender_meters=world_pos @ C.T,
                      captured_instance_world_game=world)
        path = OUT / f'mesh_world_{i:04d}.npz'
        np.savez_compressed(path, **arrays)
        row.update(world_posed_npz=str(path),
                   world_posed_bounds_game_meters=[world_pos.min(axis=0).tolist(), world_pos.max(axis=0).tolist()],
                   exact_index_draw_bindings=[{k: d[k] for k in ('sequence', 'command_index', 'commandlist_uid', 'pipeline_uid', 'captured_index_buffer')}
                                              for d in draws if d['source_name'] == row['name']])
    doc.update(instance_world_status='Recovered from actual captured indexed-draw instance SRV; unit scale, zero translation, original yaw retained.',
               instance_world_matrix_game=world.tolist(),
               instance_resource_uid=instance['instance_resource_uid'],
               instance_resource_offset=instance['instance_resource_offset'],
               instance_world_ue_yaw_degrees=math.degrees(math.atan2(world[2, 0], world[0, 0])),
               exact_index_draw_matches=instance['actual_indexed_draw_matches'],
               exact_index_matched_subsets=instance['source_subsets_with_exact_index_match'],
               world_pose_usage='Use world_posed_npz posed_world_positions_blender_meters with identity actor transform, or skin-only posed_npz plus captured_instance_world_game. Do not apply both.')
    text = json.dumps(doc, indent=2)
    for path in (OUT / 'captured_fg_stage_manifest.json', REPORT / 'CAPTURE_FG_STAGE_VALIDATION.json'):
        temporary = path.with_suffix('.tmp')
        temporary.write_text(text, encoding='utf-8')
        temporary.replace(path)
    print(json.dumps({k: doc[k] for k in ('meshes', 'vertices', 'exact_index_draw_matches', 'exact_index_matched_subsets', 'instance_world_ue_yaw_degrees', 'world_pose_usage')}, indent=2))


if __name__ == '__main__':
    main()
