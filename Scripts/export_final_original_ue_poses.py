import unreal
import json
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
clips=[('ellie-prone-lg-aim-strafe-0-fw','Ellie_Patrol_Original_0FW_AnimationCarrier_Anim',80,'original_0fw_ue_poses.json'),
       ('model-viewer-ellie-16-patrol','Ellie16_Patrol_OriginalViewerPose_UEHoldCarrier_Anim',2,'original_viewer_ue_poses.json')]
def transform(t):
    return {'translation':list(t.translation.to_tuple()),'rotation_xyzw':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],
            'scale':list(t.scale3d.to_tuple())}
for clip,name,count,filename in clips:
    path='/Game/TLOU2/CaptureMatched1152/Animations/'+name
    anim=unreal.load_asset(path)
    assert isinstance(anim,unreal.AnimSequence),path
    source=json.loads((ROOT/'Exports/AnimationSources/DecodedOriginal'/(clip+'.json')).read_text())
    names=list(dict.fromkeys(['SK_Ellie_Patrol_Exact','root']+[t['bone_name'] for t in source['tracks']]))
    opts=unreal.AnimPoseEvaluationOptions()
    opts.set_editor_property('evaluation_type',unreal.AnimDataEvalType.RAW)
    opts.set_editor_property('should_retarget',False)
    opts.set_editor_property('extract_root_motion',False)
    ref=anim.get_skeleton().get_reference_pose()
    out={'asset':path,'skeleton':anim.get_skeleton().get_path_name(),'seconds':anim.get_play_length(),
         'reference':{n:transform(ref.get_bone_pose(n)) for n in names},'frames':[]}
    for frame in range(count):
        pose=anim.get_anim_pose_at_frame(frame,opts)
        out['frames'].append({'frame':frame,'valid':pose.is_valid(),'bones':{n:transform(pose.get_bone_pose(n)) for n in names}})
    (ROOT/'Exports'/filename).write_text(json.dumps(out,indent=2))
    unreal.log('FINAL_ORIGINAL_POSE_EXPORT '+filename+' '+str(count))
