"""Compare DCC evaluated vertices against independent raw PAK/GPU skinning."""
import bpy
import json
import hashlib
import numpy as np
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
reference=ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json'
doc=json.loads(reference.read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'))
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
graph=bpy.context.evaluated_depsgraph_get()
rows=[]
manifest=json.loads((ROOT/'Exports/captured_skin_pose_chunk_manifest.json').read_text())
chunk_map={m['source_mesh']:name for name,chunk in manifest['chunks'].items() for m in chunk['meshes']}
for source in doc['rows']:
    matches=[o for o in bpy.data.objects if o.type=='MESH' and o.get('source_submesh')==source['source_mesh']
             and len(o.data.vertices)==source['vertices']]
    assert len(matches)==1, (source['source_mesh'], [o.name for o in matches])
    obj=matches[0]
    original=np.load(source['source_npz'])
    capture=json.loads(Path(source['source_capture']).read_text())
    part=next(m for m in capture['meshes'] if m['name']==source['source_mesh'])
    referenced=np.unique(original['indices_raw'].view({4:'<u2',5:'<u4'}[part['index_type']]))
    expected=np.load(source['path'])['captured_skinned_actor_vertices_blender']
    evaluated=obj.evaluated_get(graph)
    mesh=evaluated.to_mesh()
    try:
        actual=np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
        assert actual.shape==expected.shape
        errors=np.linalg.norm(actual-expected,axis=1)
        rows.append({'mesh':obj.name,'source_mesh':source['source_mesh'],'raw_reference':source['path'],'chunk':chunk_map[obj.name],
                     'referenced_vertex_ids':referenced.tolist(),'referenced_vertices':len(referenced),
                     'vertices':len(actual),'maximum_error_m':float(errors.max()),'mean_error_m':float(errors.mean())})
    finally: evaluated.to_mesh_clear()
out={'source_blend':str(ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'),'reference':str(reference),
     'source_blend_sha256':hashlib.sha256((ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend').read_bytes()).hexdigest(),
     'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
     'mesh_count':len(rows),'vertices':sum(r['vertices'] for r in rows),
     'maximum_error_m':max(r['maximum_error_m'] for r in rows),'rows':rows,
     'method':'Independent raw PAK positions and original packed22/10 orfloat32/u32 weights plus captured GPU palettes compared to fully evaluated Blender skin and corrective morph.',
     'pass':all(r['maximum_error_m']<1e-5 for r in rows)}
(ROOT/'Exports/captured_pose_independent_raw_vertex_validation.json').write_text(json.dumps(out,indent=2))
(ROOT/'Exports/captured_chunk_source_vertex_map.json').write_text(json.dumps({'source_manifest':str(ROOT/'Exports/captured_skin_pose_chunk_manifest.json'),'rows':rows},indent=2))
print('CAPTURE_RAW_VERTEX_VERIFY '+json.dumps({k:v for k,v in out.items() if k!='rows'}))
if not out['pass']: raise RuntimeError('Captured DCC vertices differ from independent raw source skinning')
