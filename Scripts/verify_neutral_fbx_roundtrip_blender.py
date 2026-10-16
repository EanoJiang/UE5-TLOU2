"""Independent Blender FBX reimport: skin membership and reference matrices."""
import bpy,json,math
from mathutils import Matrix
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx')
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.objects if o.type=='MESH']
rest=json.load(open(ROOT+'/Exports/Ellie_AugmentedBindRest_SourceMatrices.json'))
assert len(arm.data.bones)==1152,len(arm.data.bones)
assert len(meshes)==29,len(meshes)
matrix_error=0
for row in rest['rows']:
    actual=arm.matrix_world@arm.data.bones[row['bone_name']].matrix_local
    expected=Matrix(row['global_matrix_blender_meters'])
    matrix_error=max(matrix_error,max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4)))
reports=[]
for mesh in meshes:
    active=0
    error=0
    for v in mesh.data.vertices:
        weighted=[g for g in v.groups if g.weight>0]
        active=max(active,len(weighted))
        error=max(error,abs(sum(g.weight for g in weighted)-1))
        assert all(mesh.vertex_groups[g.group].name in arm.data.bones for g in weighted)
    reports.append({'mesh':mesh.name,'vertices':len(mesh.data.vertices),'max_influences':active,'max_weight_sum_error':error})
out={'file':ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx','armature':arm.name,
     'bones':len(arm.data.bones),'mesh_count':len(meshes),'export_vertices':sum(r['vertices'] for r in reports),
     'max_influences':max(r['max_influences'] for r in reports),
     'weight_sum_max_error':max(r['max_weight_sum_error'] for r in reports),
     'reference_matrix_max_error':matrix_error,'meshes':reports}
out['pass']=out['max_influences']==12 and out['weight_sum_max_error']<2e-6 and matrix_error<1e-4
json.dump(out,open(ROOT+'/Exports/neutral_fbx_roundtrip_validation.json','w'),indent=2)
print('NEUTRAL_FBX_ROUNDTRIP',json.dumps({k:v for k,v in out.items() if k!='meshes'}))
if not out['pass']:raise RuntimeError('FBX roundtrip failed')
