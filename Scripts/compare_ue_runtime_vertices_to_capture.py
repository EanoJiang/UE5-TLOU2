"""Compare actual UE CPU skin+enabled morph positions to raw PAK/GPU results.

FBX and UE split/merge vertices at UV/material boundaries, so use bidirectional
nearest distances and report both point counts. Source vertex indices are not
assumed to survive the importer. Positions are compared in component space.
"""
import argparse
import hashlib
import json
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree

ROOT=Path('D:/TLOU2_UE5_8_Codex')
TOLERANCE_M=0.0001
parser=argparse.ArgumentParser()
parser.add_argument('dump',type=Path)
args=parser.parse_args()
reference=ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json'
source_reference_bytes=reference.read_bytes()
source=json.loads(source_reference_bytes)
mapping=json.loads((ROOT/'Exports/captured_chunk_source_vertex_map.json').read_text())
dump_path=args.dump/'ue_runtime_vertex_dump.json'
dump_bytes=dump_path.read_bytes()
dump=json.loads(dump_bytes)
corrective_policy=json.loads((ROOT/'Exports/captured_corrective_curve_validation.json').read_text())
required_correctives={r['chunk']:r['required_above_10um'] for r in corrective_policy['meshes']}
expected_by_chunk={}
shader_by_chunk={}
influences_by_chunk={}
triangles_by_chunk={}
source_by_path={str(Path(row['path']).resolve()).casefold():row for row in source['rows']}
for row in mapping['rows']:
    data=np.load(row['raw_reference'])
    chunk=row['chunk']
    referenced=row['referenced_vertex_ids']
    expected_by_chunk.setdefault(chunk,[]).append(data['captured_skinned_actor_vertices_blender'][referenced]*np.array((100.,-100.,100.)))
    shader_by_chunk.setdefault(chunk,[]).append(data['original_shader_weight_skinned_actor_vertices_blender'][referenced]*np.array((100.,-100.,100.)))
    count=int(np.count_nonzero(data['normalized_source_weights'][referenced],axis=1).max())
    influences_by_chunk[chunk]=max(influences_by_chunk.get(chunk,0),count)
    original=source_by_path[str(Path(row['raw_reference']).resolve()).casefold()]
    original_meta=json.loads(Path(original['source_capture']).read_text())
    original_mesh=next(m for m in original_meta['meshes'] if m['name']==original['source_mesh'])
    assert original_mesh['count']%3==0
    triangles_by_chunk[chunk]=triangles_by_chunk.get(chunk,0)+original_mesh['count']//3
assert sum(triangles_by_chunk.values())==117459
expected_by_chunk={name:np.concatenate(arrays) for name,arrays in expected_by_chunk.items()}
shader_by_chunk={name:np.concatenate(arrays) for name,arrays in shader_by_chunk.items()}
actual_by_chunk={}
mesh_rows=[]
checks={}
for row in dump['meshes']:
    chunk=row['mesh'].split('/CapturedMeshes/',1)[1].split('/',1)[0]
    assert chunk not in actual_by_chunk and chunk in expected_by_chunk, 'Unexpected or duplicate UE chunk: '+chunk
    expected=expected_by_chunk[chunk]
    positions_bytes=Path(row['positions']).read_bytes()
    p=np.frombuffer(positions_bytes,dtype='<f4').reshape(-1,3).astype(np.float64)
    assert len(p)==row['vertices'] and np.isfinite(p).all()
    distances,_=cKDTree(expected).query(p,workers=-1)
    reverse,_=cKDTree(p).query(expected,workers=-1)
    shader_forward,_=cKDTree(shader_by_chunk[chunk]).query(p,workers=-1)
    shader_reverse,_=cKDTree(p).query(shader_by_chunk[chunk],workers=-1)
    correctives={n:v for n,v in row.get('morphs',{}).items() if 'CaptureAffineCorrective' in n}
    checks[chunk+'_morphs_enabled']=(bool(correctives) or not required_correctives[chunk]) and all(abs(v-1)<1e-6 for v in correctives.values())
    checks[chunk+'_influence_capacity']=row.get('maximum_bone_influences',0)>=influences_by_chunk[chunk]
    checks[chunk+'_actor_translation']=max(abs(a-b) for a,b in zip(row['component_location_cm'],(-3.2344385733,1.7656933532,.00007932785)))<1e-3
    checks[chunk+'_actor_rotation']=max(abs(a-b) for a,b in zip(row['component_rotation_degrees'],(0,4.8182263022,0)))<1e-3
    checks[chunk+'_actor_scale']=max(abs(a-1) for a in row['component_scale'])<1e-6
    checks[chunk+'_vertices_match']=max(distances.max(),reverse.max())/100<TOLERANCE_M
    checks[chunk+'_shader_vertices_match']=max(shader_forward.max(),shader_reverse.max())/100<TOLERANCE_M
    checks[chunk+'_original_triangle_count']=row.get('triangles')==triangles_by_chunk[chunk]
    checks[chunk+'_original_index_count']=row.get('index_count')==triangles_by_chunk[chunk]*3
    checks[chunk+'_render_section_triangle_count']=row.get('render_section_triangles')==triangles_by_chunk[chunk]
    mesh_rows.append({'chunk':chunk,'mesh':row['mesh'],'vertices':len(p),'raw_source_vertices':len(expected),
                      'positions_binary':str(Path(row['positions']).resolve()),
                      'positions_binary_sha256':hashlib.sha256(positions_bytes).hexdigest(),
                      'source_triangles':triangles_by_chunk[chunk],'ue_runtime_triangles':row.get('triangles'),
                      'ue_runtime_index_count':row.get('index_count'),
                      'ue_runtime_render_section_triangles':row.get('render_section_triangles'),
                      'ue_to_source_max_distance_m':float(distances.max()/100),'source_to_ue_max_distance_m':float(reverse.max()/100),
                      'bidirectional_max_distance_m':float(max(distances.max(),reverse.max())/100),
                      'original_shader_bidirectional_max_distance_m':float(max(shader_forward.max(),shader_reverse.max())/100),
                      'mean_distance_m':float(distances.mean()/100),
                      'maximum_bone_influences':row.get('maximum_bone_influences'),
                      'source_maximum_bone_influences':influences_by_chunk[chunk],
                      'capture_corrective_required_above_10um':required_correctives[chunk],
                      'morphs':row.get('morphs',{})})
    actual_by_chunk[chunk]=p
checks['exact_selected_chunk_identities']=set(actual_by_chunk)==set(expected_by_chunk)
checks['exact_original_character_triangle_total']=dump.get('character_triangles')==117459
checks['exact_original_character_index_total']=dump.get('character_index_count')==117459*3
checks['exact_character_chunk_count']=dump.get('character_chunk_count')==len(expected_by_chunk)
checks['reported_character_triangle_sum_consistent']=dump.get('character_triangles')==sum(r.get('triangles',0) for r in dump['meshes'])
checks['reported_character_index_sum_consistent']=dump.get('character_index_count')==sum(r.get('index_count',0) for r in dump['meshes'])
checks['exact_camera_location']=max(abs(a-b) for a,b in zip(dump['camera_location_cm'],(0,300,115)))<1e-3
checks['exact_camera_forward']=max(abs(a-b) for a,b in zip(dump['camera_forward'],(.0000026097,-.983470887,-.181064765)))<1e-5
checks['exact_camera_horizontal_fov']=abs(dump['camera_horizontal_fov_degrees']-79.9908974)<1e-3
checks={name:bool(value) for name,value in checks.items()}
max_error=max(r['bidirectional_max_distance_m'] for r in mesh_rows)
report={'raw_source_reference':str(reference),'ue_runtime_dump':str(args.dump/'ue_runtime_vertex_dump.json'),
        'source_reference_sha256':hashlib.sha256(source_reference_bytes).hexdigest(),
        'ue_runtime_dump_sha256':hashlib.sha256(dump_bytes).hexdigest(),
        'source_vertices':sum(len(p) for p in expected_by_chunk.values()),'ue_render_vertices':sum(len(p) for p in actual_by_chunk.values()),'meshes':mesh_rows,
        'source_allocated_vertices':source['selected_character_vertex_count'],
        'source_triangles':sum(triangles_by_chunk.values()),'ue_runtime_triangles':dump.get('character_triangles'),
        'ue_runtime_index_count':dump.get('character_index_count'),
        'source_referenced_vertex_policy':'Only original triangle-index referenced vertices require render-surface coverage.592 unreferenced head buffer positions are preserved in DCC/source audit, correctly omitted by render exporters.',
        'bidirectional_max_distance_m':max_error,
        'original_shader_bidirectional_max_distance_m':max(r['original_shader_bidirectional_max_distance_m'] for r in mesh_rows),
        'tolerance_m':TOLERANCE_M,'checks':checks,'pass':all(checks.values()),
        'method':'Bidirectional component-space point-cloud distance per authoritative selected chunk, plus exact chunk identities, original per-chunk and total runtime triangle/index counts, influence capacity, enabled morphs, actor-world transform and captured camera checks. UE GetCPUSkinnedVertices includes enabled morph targets; raw reference uses original PAK positions/weights and captured GPU matrices.',
        'precision_note':'UE bone TRS and imported quantized skin-weight precision are evaluated here; original GPU palette bytes are preserved separately.'}
(ROOT/'Exports/ue_runtime_capture_vertex_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='meshes'},indent=2))
if not report['pass']: raise RuntimeError('UE runtime capture verification failed; see individual checks')
