"""Independently reimport FBX carrier and compare basis-invariant skin matrices."""
import bpy,json
from pathlib import Path
from mathutils import Matrix
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/BoneDeformationDiagnostic'
source=json.loads((OUT/'blender_capture_bones1152.json').read_text())
byname={r['bone']:r for r in source['rows']}
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx=ROOT/'Exports/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier.fbx'
bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=True,automatic_bone_orientation=False)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
frames=[]
if arm.animation_data and arm.animation_data.action:
    action=arm.animation_data.action
    try:frames=[float(action.frame_range[0]),float(action.frame_range[1])]
    except Exception:pass
assert frames, 'FBX animation missing'
bpy.context.scene.frame_set(int(frames[0]))
bpy.context.view_layer.update()
rows=[]
for bone in arm.data.bones:
    if bone.name not in byname:continue
    r=byname[bone.name]
    original=Matrix(r['pose_global_blender_m'])@Matrix(r['rest_global_blender_m']).inverted()
    imported=arm.pose.bones[bone.name].matrix@bone.matrix_local.inverted()
    error=max(abs(original[i][j]-imported[i][j])for i in range(4)for j in range(4))
    rows.append({'bone':bone.name,'skin_matrix_max_error':error,
        'source_pose_global':r['pose_global_blender_m'],
        'source_rest_global':r['rest_global_blender_m'],
        'imported_pose_global':[[float(x)for x in row]for row in arm.pose.bones[bone.name].matrix],
        'imported_rest_global':[[float(x)for x in row]for row in bone.matrix_local]})
doc={'fbx':str(fbx),'bones':len(arm.data.bones),'compared_source_bones':len(rows),
    'imported_frames':frames,'maximum_skin_matrix_error':max(r['skin_matrix_max_error']for r in rows),
    'largest_errors':sorted([(r['bone'],r['skin_matrix_max_error'])for r in rows],key=lambda r:r[1],reverse=True)[:30],
    'rows':rows}
(OUT/'blender_reimported_capture_fbx_bones.json').write_text(json.dumps(doc,indent=2))
print('FBX_CARRIER_BONE_DIAGNOSTIC '+json.dumps({k:v for k,v in doc.items()if k!='rows'}))
