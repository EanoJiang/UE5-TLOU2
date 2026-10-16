import unreal,json
paths=['/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim','/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim']
out={}
for p in paths:
 a=unreal.load_asset(p);d={'path':p};
 try: opts=unreal.AnimPoseEvaluationOptions(); d['opts']=str(opts.to_dict());
 except Exception as e:d['opts_err']=repr(e);opts=None
 for f in [0,1,10,40,79]:
  try:
   pose=a.get_anim_pose_at_frame(f,opts); pd={'repr':str(pose)[:200],'class':str(pose.__class__)}
   for name in ['is_valid','get_bone_names','get_bone_pose','get_ref_bone_pose']:
    try:
     if name=='get_bone_pose':
      bn=pose.get_bone_names();pd['bone_names_head']=[str(x) for x in bn[:5]];pd['bone_count']=len(bn);pd['bone0']=str(pose.get_bone_pose(bn[0]))
     else:pd[name]=str(getattr(pose,name)())[:500]
    except Exception as e:pd[name+'_err']=repr(e)
   d['frame'+str(f)]=pd
  except Exception as e:d['frame'+str(f)]='ERR '+repr(e)
 out[p]=d
open('D:/TLOU2_UE5_8_Codex/Exports/anim_pose_eval.json','w').write(json.dumps(out,indent=2,default=str));print(json.dumps(out,indent=2,default=str))
