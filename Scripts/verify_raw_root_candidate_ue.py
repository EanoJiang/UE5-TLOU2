import unreal,json
p='/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim'; anim=unreal.load_asset(p);out={'asset':p,'class':anim.get_class().get_name() if anim else None}
for prop in ['sequence_length','number_of_frames','num_frames','rate_scale','skeleton','enable_root_motion','root_motion_root_lock','root_motion_translation','root_motion_rotation','additive_anim_type']:
 try:out[prop]=str(anim.get_editor_property(prop))
 except Exception as e:out[prop]='ERR '+str(e)
try:out['bone_count']=len(anim.get_editor_property('skeleton').get_reference_pose().get_bone_names())
except Exception as e:out['bone_err']=str(e)
for frame in [0,1,10,40,79]:
 try:
  p0=anim.get_bone_transform(0,frame,0);out['bone0_'+str(frame)]=str(p0)
 except Exception as e:out['bone0_'+str(frame)]='ERR '+str(e)
open('D:/TLOU2_UE5_8_Codex/Exports/raw_root_candidate_ue_verify.json','w').write(json.dumps(out,indent=2,default=str));unreal.log('RAW_ROOT_VERIFY_DONE')
