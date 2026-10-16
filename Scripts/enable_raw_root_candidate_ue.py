import unreal,json
p='/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim';a=unreal.load_asset(p); out={}
for name,val in [('enable_root_motion',True),('root_motion_root_lock',unreal.RootMotionRootLock.ZERO)]:
 try:a.set_editor_property(name,val);out[name]='set'
 except Exception as e:out[name]=str(e)
try:unreal.EditorAssetLibrary.save_asset(p,only_if_is_dirty=False);out['saved']=True
except Exception as e:out['saved']=str(e)
open('D:/TLOU2_UE5_8_Codex/Exports/raw_root_candidate_ue_rootmotion_result.json','w').write(json.dumps(out,indent=2));unreal.log('RAW_ROOT_ENABLE_DONE')
