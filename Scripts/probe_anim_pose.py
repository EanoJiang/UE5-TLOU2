import unreal,json
paths=['/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim','/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim']
out={}
for p in paths:
 a=unreal.load_asset(p);d={'path':p}
 for name,args in [('get_anim_pose_at_frame',(0,)),('get_anim_pose_at_frame',(40,)),('get_anim_pose_at_time',(0.0,)),('get_anim_pose_at_time',(1.0,)),('get_skeleton',()),('get_play_length',())]:
  try:
   v=getattr(a,name)(*args);d[name+str(args)]=str(v)[:2000];
   if hasattr(v,'__len__'): d[name+str(args)+'len']=len(v)
  except Exception as e:d[name+str(args)]='ERR '+repr(e)
 out[p]=d
open('D:/TLOU2_UE5_8_Codex/Exports/anim_pose_probe.json','w').write(json.dumps(out,indent=2,default=str)); print(json.dumps(out,indent=2,default=str))
