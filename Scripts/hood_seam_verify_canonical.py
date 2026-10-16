"""Compare implicated source vertices against the saved canonical DCC model."""
import bpy
import json
from pathlib import Path
import numpy as np

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/HoodSeam'

def main():
    rows=json.loads((ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json').read_text())['rows']
    trace=json.loads((OUT/'source_triangle_layers.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'))
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    reports=[]
    for folder in ('ellie_head','ellie_patrol_hoodie_cloth'):
        for row in (r for r in rows if r['source_folder']==folder):
            objects=[o for o in bpy.data.objects if o.type=='MESH' and o.get('source_submesh')==row['source_mesh'] and o.get('source_pak')==row['source_pak']]
            if not objects:continue
            obj=objects[0]
            evaluated=obj.evaluated_get(depsgraph)
            mesh=evaluated.to_mesh()
            try:actual=np.array([v.co[:] for v in mesh.vertices])
            finally:evaluated.to_mesh_clear()
            reference=np.load(row['path'])
            target=reference['captured_skinned_actor_vertices_blender']
            assert len(actual)==len(target)
            errors=np.linalg.norm(actual-target,axis=1)
            entry=dict(source_mesh=row['source_mesh'],vertices=len(actual),max_normalized_source_vertex_error_m=float(errors.max()))
            if row['source_mesh']==trace['head_source_mesh']:
                ids=[v['vertex'] for v in trace['source_vertex_weights']]
                entry['implicated_vertices']=ids
                entry['implicated_vertex_error_m']=errors[ids].tolist()
            reports.append(entry)
    report=dict(pass_=all(r['max_normalized_source_vertex_error_m']<1e-5 for r in reports),meshes=reports,
        source_blend=str(ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'))
    report['pass']=report.pop('pass_')
    (OUT/'canonical_geometry_verification.json').write_text(json.dumps(report,indent=2))
    print('HOOD_SEAM_CANONICAL_COMPARE '+json.dumps(report))

if __name__=='__main__':main()
