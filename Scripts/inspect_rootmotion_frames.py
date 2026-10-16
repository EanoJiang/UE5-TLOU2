import unreal,json
anim=unreal.load_asset('/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim'); out={}; opts=unreal.AnimPoseEvaluationOptions(); opts.set_editor_property('evaluation_type',unreal.AnimDataEvalType.RAW)
for frame in [0,1,10,40,79]:
 try:
  p=anim.get_anim_pose_at_frame(frame,opts); names=p.get_bone_names(); d={'names_count':len(names)}
  for n in ['SK_Ellie_Patrol_Exact','root','pelvis']:
   try:d[n]=str(p.get_bone_pose(n))
   except Exception as e:d[n]='ERR '+str(e)
  out[str(frame)]=d
 except Exception as e: out[str(frame)]={'err':str(e)}
open('D:/TLOU2_UE5_8_Codex/Exports/rootmotion_pose_frames.json','w').write(json.dumps(out,indent=2,default=str))
