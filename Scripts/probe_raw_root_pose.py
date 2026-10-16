import unreal,json
p='/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim'; a=unreal.load_asset(p); opts=unreal.AnimPoseEvaluationOptions(); names=[str(n) for n in a.get_anim_pose_at_frame(0,opts).get_bone_names()];out=[]
for f in [0,1,2,10,40,79]:
 pose=a.get_anim_pose_at_frame(f,opts);row={'frame':f}
 for target in ['SK_Ellie_Patrol_Exact','root','spinea']:
  t=pose.get_bone_pose(target);v=t.translation
  row[target]={'x':float(v.x),'y':float(v.y),'z':float(v.z)}
 out.append(row)
json.dump({'bone_count':len(names),'first_names':names[:5],'rows':out},open('D:/TLOU2_UE5_8_Codex/Exports/raw_root_pose_samples.json','w'),indent=2)
print(json.dumps(out,indent=2))
