"""Read-only UE source/raw/compressed poses and mesh-specific reference data."""
import unreal
import json
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/BoneDeformationDiagnostic'
OUT.mkdir(exist_ok=True)
animpath='/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim'
anim=unreal.load_asset(animpath)
assert isinstance(anim,unreal.AnimSequence),animpath

def transform(t):
    return {'translation':list(t.translation.to_tuple()),
        'rotation_xyzw':[float(t.rotation.x),float(t.rotation.y),float(t.rotation.z),float(t.rotation.w)],
        'scale':list(t.scale3d.to_tuple())}

def bones(pose):
    names=[str(n)for n in pose.get_bone_names()]
    return {n:{'local':transform(pose.get_bone_pose(n,unreal.AnimPoseSpaces.LOCAL)),
        'global':transform(pose.get_bone_pose(n,unreal.AnimPoseSpaces.WORLD)),
        'reference_local':transform(pose.get_ref_bone_pose(n,unreal.AnimPoseSpaces.LOCAL)),
        'reference_global':transform(pose.get_ref_bone_pose(n,unreal.AnimPoseSpaces.WORLD))}for n in names}

ref=anim.get_skeleton().get_reference_pose()
doc={'asset':animpath,'skeleton':anim.get_skeleton().get_path_name(),'seconds':anim.get_play_length(),
    'skeleton_reference':bones(ref),'evaluations':{},'mesh_evaluations':{}}
for label,kind,retarget in [('source_unretargeted',unreal.AnimDataEvalType.SOURCE,False),
    ('raw_unretargeted',unreal.AnimDataEvalType.RAW,False),('raw_retargeted',unreal.AnimDataEvalType.RAW,True),
    ('compressed_unretargeted',unreal.AnimDataEvalType.COMPRESSED,False),
    ('compressed_retargeted',unreal.AnimDataEvalType.COMPRESSED,True)]:
    opts=unreal.AnimPoseEvaluationOptions()
    opts.set_editor_property('evaluation_type',kind)
    opts.set_editor_property('should_retarget',retarget)
    opts.set_editor_property('extract_root_motion',False)
    pose=anim.get_anim_pose_at_frame(0,opts)
    assert pose.is_valid(),label
    doc['evaluations'][label]=bones(pose)
    unreal.log('CAPTURE_BONE_DIAGNOSTIC '+label+' '+str(len(doc['evaluations'][label])))
for chunk in ['body_clothing','head_face','hair','backpack','accessories']:
    path='/Game/TLOU2/CaptureMatched1152/CapturedMeshes/'+chunk+'/Ellie_Patrol_'+chunk+'_Pruned'
    mesh=unreal.load_asset(path)
    assert isinstance(mesh,unreal.SkeletalMesh),path
    opts=unreal.AnimPoseEvaluationOptions()
    opts.set_editor_property('evaluation_type',unreal.AnimDataEvalType.COMPRESSED)
    opts.set_editor_property('should_retarget',True)
    opts.set_editor_property('extract_root_motion',False)
    opts.set_editor_property('optional_skeletal_mesh',mesh)
    pose=anim.get_anim_pose_at_frame(0,opts)
    assert pose.is_valid(),chunk
    doc['mesh_evaluations'][chunk]={'mesh':path,'bones':bones(pose)}
    unreal.log('CAPTURE_BONE_DIAGNOSTIC mesh '+chunk+' '+str(len(doc['mesh_evaluations'][chunk]['bones'])))
(OUT/'ue_capture_bone_poses.json').write_text(json.dumps(doc,indent=2))
unreal.log('CAPTURE_BONE_DIAGNOSTIC_DONE '+str(OUT/'ue_capture_bone_poses.json'))
