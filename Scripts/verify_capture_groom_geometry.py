"""Validate exported strand data and its agreement with the actual UE import."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom'
data_path = OUT / 'Ellie_Patrol_CaptureGroom_curves.npz'
data = np.load(data_path)
points = data['positions_cm']
lengths = np.linalg.norm(np.diff(points, axis=1), axis=2).sum(axis=1)
counts = {int(k): int(np.sum(data['group_ids'] == k)) for k in np.unique(data['group_ids'])}
bounds = [points.min((0, 1)).tolist(), points.max((0, 1)).tolist()]
checks = {
    'all_coordinates_finite': bool(np.isfinite(points).all()),
    'nonzero_strand_lengths': bool(lengths.min() > .19),
    'four_groups_present': set(counts) == {0, 1, 2, 3},
    'centimeter_conversion': bool(np.max(np.abs(points - data['positions_blender_m'] * np.array([100, -100, 100]))) < .00002),
    'vertex_counts_match': bool(np.all(data['curve_vertex_counts'] == points.shape[1])),
    'plausible_hair_diameters': bool(np.min(data['widths_mm']) >= .03 and np.max(data['widths_mm']) <= .09),
    'captured_head_height': bool(135 < bounds[0][2] < 150 and 160 < bounds[1][2] < 175),
}
manifest_path = OUT / 'groom_manifest.json'
if manifest_path.is_file():
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    checks['manifest_counts_match'] = manifest['curve_count'] == len(points) and manifest['point_count'] == int(np.prod(points.shape[:2]))
import_path = OUT / 'ue_groom_import_result.json'
if import_path.is_file():
    imported = json.loads(import_path.read_text(encoding='utf-8'))
    checks['ue_import_passed'] = bool(imported['pass'])
    checks['ue_curve_count_matches'] = imported.get('curve_count') == len(points)
    checks['ue_built_point_count_includes_one_extra_ending_point_per_curve'] = imported.get('point_count') == len(points) * (points.shape[1] + 1)
    checks['ue_group_counts_match'] = {int(g['group_id']): int(g['num_curves']) for g in imported.get('groups', [])} == counts

report = {'pass': all(checks.values()), 'checks': checks,
          'curve_count': len(points), 'point_count': int(np.prod(points.shape[:2])),
          'groups': counts, 'bounds_ue_cm': bounds,
          'length_cm_min_median_max': np.percentile(lengths, [0, 50, 100]).tolist(),
          'width_mm_min_median_max': np.percentile(data['widths_mm'], [0, 50, 100]).tolist(),
          'npz_sha256': hashlib.sha256(data_path.read_bytes()).hexdigest()}
(OUT / 'geometry_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
assert report['pass'], report
