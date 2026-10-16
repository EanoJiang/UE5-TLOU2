"""Check final reference assets using independent scalar matrix arithmetic."""
from pathlib import Path
import json
import math
import numpy as np

ROOT=Path('D:/TLOU2_UE5_8_Codex')
CAP=ROOT/'Exports/CaptureBuffers'
REPORT=CAP/'IndependentSkinnedMeshes/selected29_independent_skinning_report.json'
doc=json.loads(REPORT.read_text())
human=np.load(CAP/'Ellie_Capture_SkinPalette1038.npz')['captured_skin_actor_game']
hoodie=np.load(CAP/'Capture_Hoodie_SkinPalette75.npz')['captured_skin_actor_game']
bindings=json.loads((ROOT/'Content/TLOU2/Reports/CAPTURE_MESH_SOURCE_BINDING_VALIDATION.json').read_text())
matched={(r['source_pak'],r['source_submesh'])for r in bindings['rows']if r['actual_dispatch_exact_matches']}
rows=[]
for row in doc['rows']:
    with np.load(row['path'])as archive:
        z={k:archive[k]for k in archive.files}
    raw=np.load(row['source_npz'])
    meta=json.loads(Path(row['source_capture']).read_text())
    mesh=next(r for r in meta['meshes']if r['name']==row['source_mesh'])
    n=row['vertices']
    raw_ids=raw['bidx_raw'].view('<u2'if mesh['bindings']['bidx']['type']==4 else '<u4')[:n*12].reshape(n,12)
    raw_weights=raw['bwgt_raw'].view('<f4'if mesh['bindings']['bwgt']['type']==0 else '<u4')[:n*12].reshape(n,12)
    assert np.array_equal(raw_ids,z['source_bone_indices_typed'])
    assert np.array_equal(raw_weights,z['source_weight_values_typed'])
    assert (row['source_pak'],row['source_mesh'])in matched, row['source_mesh']
    assert np.isfinite(z['captured_skinned_actor_vertices_game']).all()
    assert np.isfinite(z['original_shader_weight_skinned_actor_vertices_game']).all()
    palette=hoodie if row['joint_palette_owner']=='hoodie_owned78'else human
    samples=sorted(set([0,n-1,*np.linspace(0,n-1,23,dtype=int).tolist()]))
    error=0.0
    shader_error=0.0
    for vertex in samples:
        v=z['source_vertices_game'][vertex].tolist()+[1.0]
        for weight_key,result_key,mode in [
            ('normalized_source_weights','captured_skinned_actor_vertices_game','normalized'),
            ('original_shader_weights_float32','original_shader_weight_skinned_actor_vertices_game','shader')]:
            expected=[]
            for axis in range(3):
                value=math.fsum(float(z[weight_key][vertex,j])*math.fsum(float(palette[int(z['source_bone_indices'][vertex,j]),axis,k])*v[k]for k in range(4))for j in range(12))
                expected.append(value)
            delta=max(abs(expected[k]-float(z[result_key][vertex,k]))for k in range(3))
            if mode=='normalized':error=max(error,delta)
            else:shader_error=max(shader_error,delta)
    assert error<1e-12 and shader_error<1e-12,(row['source_mesh'],error,shader_error)
    rows.append({'source_mesh':row['source_mesh'],'vertices':n,'sampled_vertices':len(samples),
        'original_typed_joint_and_weight_arrays_exact':True,'actual_capture_skin_binding_match':True,
        'normalized_lbs_scalar_max_error_m':error,'original_shader_lbs_scalar_max_error_m':shader_error})
result={'reference_report':str(REPORT),'selected_meshes':len(rows),'vertices':sum(r['vertices']for r in rows),
    'sampled_vertices':sum(r['sampled_vertices']for r in rows),
    'all_source_typed_arrays_bit_exact':True,'all_actual_capture_skin_bindings_exact':True,
    'normalized_lbs_scalar_max_error_m':max(r['normalized_lbs_scalar_max_error_m']for r in rows),
    'original_shader_lbs_scalar_max_error_m':max(r['original_shader_lbs_scalar_max_error_m']for r in rows),
    'method':'Full source typed-array equality and actual binding association for every selected mesh; independently coded scalar math.fsum matrix/LBS verification of23 distributed vertices per mesh.',
    'pass':True,'rows':rows}
(CAP/'IndependentSkinnedMeshes/selected29_reference_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
