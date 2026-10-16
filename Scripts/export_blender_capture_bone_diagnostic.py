"""Export the exact source reference and evaluated captured local/global bones.

Also test Unreal's positive-scale FTransform composition formula independently
against the full matrix bone chain used by Blender.
"""
import bpy
import json
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/BoneDeformationDiagnostic'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'))
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
names=[b.name for b in arm.data.bones]
assert len(names)==1152,len(names)
# Blender -> UE basis; positions convert meters to centimeters.
U=Matrix.Diagonal((100.,-100.,100.,1.))
Uinv=U.inverted()
def array(m):return [[float(x)for x in r]for r in m]
def sqt(m):
    t,q,s=m.decompose()
    return {'translation':list(t),'rotation_xyzw':[q.x,q.y,q.z,q.w],'scale':list(s)}
def error(a,b):return max(abs(a[i][j]-b[i][j])for i in range(4)for j in range(4))
rows=[]
pose_trs={}
rest_trs={}
for bone in arm.data.bones:
    parent=bone.parent.name if bone.parent else None
    rest=bone.matrix_local.copy()
    pose=arm.pose.bones[bone.name].matrix.copy()
    restlocal=bone.parent.matrix_local.inverted()@rest if bone.parent else rest
    poselocal=arm.pose.bones[parent].matrix.inverted()@pose if parent else pose
    # The UE multiply formula is parentQ*localQ, parentScale*localScale,
    # parentQ.rotate(parentScale*localTranslation)+parentTranslation.
    for target,local in [(pose_trs,poselocal),(rest_trs,restlocal)]:
        t,q,s=local.decompose()
        assert min(s)>0,(bone.name,tuple(s))
        if parent:
            tp,qp,sp=target[parent]
            tg=tp+qp@(Vector((sp.x*t.x,sp.y*t.y,sp.z*t.z)))
            qg=qp@q
            sg=Vector((sp.x*s.x,sp.y*s.y,sp.z*s.z))
        else:tg,qg,sg=t,q,s
        target[bone.name]=(tg,qg,sg)
    pt,pq,ps=pose_trs[bone.name]
    rt,rq,rs=rest_trs[bone.name]
    predictedpose=Matrix.LocRotScale(pt,pq,ps)
    predictedrest=Matrix.LocRotScale(rt,rq,rs)
    rows.append({'bone':bone.name,'parent':parent,
        'rest_global_blender_m':array(rest),'rest_local_blender_m':array(restlocal),
        'pose_global_blender_m':array(pose),'pose_local_blender_m':array(poselocal),
        'basis_blender':array(arm.pose.bones[bone.name].matrix_basis),
        'rest_local_ue_cm':array(U@restlocal@Uinv),'rest_global_ue_cm':array(U@rest@Uinv),
        'pose_local_ue_cm':array(U@poselocal@Uinv),'pose_global_ue_cm':array(U@pose@Uinv),
        'rest_local_sqt_ue_cm':sqt(U@restlocal@Uinv),
        'pose_local_sqt_ue_cm':sqt(U@poselocal@Uinv),
        'predicted_ue_trs_chain_pose_global_blender_m':array(predictedpose),
        'predicted_ue_trs_chain_rest_global_blender_m':array(predictedrest),
        'pose_local_trs_decomposition_max_error':error(poselocal,Matrix.LocRotScale(*poselocal.decompose())),
        'predicted_ue_trs_chain_global_max_matrix_error':error(pose,predictedpose),
        'predicted_ue_trs_chain_global_translation_error_m':(pose.translation-predictedpose.translation).length})
report={'source_blend':str(ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'),
    'bones':len(rows),'synthetic_ue_armature_root':arm.name,
    'basis':'Blender(m) -> UE(cm): (x,y,z)->(100x,-100y,100z); game(m)->UE(cm):(x,y,z)->(100x,100z,100y)',
    'maximum_local_trs_decomposition_matrix_error':max(r['pose_local_trs_decomposition_max_error']for r in rows),
    'maximum_predicted_ue_trs_chain_global_matrix_error':max(r['predicted_ue_trs_chain_global_max_matrix_error']for r in rows),
    'maximum_predicted_ue_trs_chain_global_translation_error_m':max(r['predicted_ue_trs_chain_global_translation_error_m']for r in rows),
    'ue_multiply_reference':'UE5.8 Engine/Source/Runtime/Core/Public/Math/TransformNonVectorized.h:1338-1344',
    'rows':rows}
(OUT/'blender_capture_bones1152.json').write_text(json.dumps(report,indent=2))
print('BLENDER_BONE_DIAGNOSTIC '+json.dumps({k:v for k,v in report.items()if k!='rows'}))
print('LARGEST_TRS_CHAIN_ERRORS '+json.dumps(sorted([(r['bone'],r['predicted_ue_trs_chain_global_translation_error_m'],r['predicted_ue_trs_chain_global_max_matrix_error'])for r in rows],key=lambda r:r[1],reverse=True)[:20]))
