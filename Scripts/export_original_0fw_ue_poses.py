import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
path='/Game/TLOU2/CaptureMatched1074/Animations/Ellie_Original_0FW_AnimationCarrier_Anim';anim=unreal.load_asset(path)
src=json.load(open(ROOT+'/Exports/AnimationSources/DecodedOriginal/ellie-prone-lg-aim-strafe-0-fw.json'));names=[t['bone_name'] for t in src['tracks']]
opts=unreal.AnimPoseEvaluationOptions();opts.set_editor_property('evaluation_type',unreal.AnimDataEvalType.RAW);opts.set_editor_property('should_retarget',False);opts.set_editor_property('extract_root_motion',False)
def xf(t):
    return {'translation':[float(t.translation.x),float(t.translation.y),float(t.translation.z)],'rotation_xyzw':[float(t.rotation.x),float(t.rotation.y),float(t.rotation.z),float(t.rotation.w)],'scale':[float(t.scale3d.x),float(t.scale3d.y),float(t.scale3d.z)]}
out={'asset':path,'skeleton':anim.get_skeleton().get_path_name(),'seconds':anim.get_play_length(),'frames':[]}
ref=anim.get_skeleton().get_reference_pose();out['reference']={n:xf(ref.get_bone_pose(n)) for n in ['SK_Ellie_Patrol_Exact','root']+names}
for f in range(80):
    pose=anim.get_anim_pose_at_frame(f,opts)
    out['frames'].append({'frame':f,'valid':pose.is_valid(),'bones':{n:xf(pose.get_bone_pose(n)) for n in ['SK_Ellie_Patrol_Exact','root']+names}})
json.dump(out,open(ROOT+'/Exports/original_0fw_ue_poses.json','w'),indent=2)
unreal.log('ORIGINAL_0FW_UE_POSES '+str(len(out['frames'])))
