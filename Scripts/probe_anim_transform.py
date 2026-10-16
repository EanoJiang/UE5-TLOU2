import unreal,json
p='/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim'; a=unreal.load_asset(p);opts=unreal.AnimPoseEvaluationOptions();pose=a.get_anim_pose_at_frame(1,opts);out={}
for bn0 in pose.get_bone_names()[:3]:
 bn=str(bn0); t=pose.get_bone_pose(bn0);d={'str':str(t)}
 for attr in ['translation','rotation','scale3d']:
  try:
   v=getattr(t,attr);d[attr]={'str':str(v), 'x':float(v.x),'y':float(v.y),'z':float(v.z),'w':float(v.w) if hasattr(v,'w') else None}
  except Exception as e:d[attr]=repr(e)
 out[bn]=d
open('D:/TLOU2_UE5_8_Codex/Exports/anim_transform_probe.json','w').write(json.dumps(out,indent=2,default=str));print(json.dumps(out,indent=2,default=str))
