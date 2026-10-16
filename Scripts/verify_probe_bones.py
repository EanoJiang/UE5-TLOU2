import unreal, json
sk=unreal.load_asset('/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'); sm=unreal.load_asset('/Game/TLOU2/ExactBody1074/Ellie_Patrol_ExactBody')
out={}
try:
 p=sk.get_reference_pose(); out['ref_pose_len']=len(p); out['ref0']=str(p[0]) if p else None; out['ref_last']=str(p[-1]) if p else None
except Exception as e: out['pose_err']=str(e)
for objname,obj in [('sk',sk),('sm',sm)]:
 out[objname]={}
 for i in [0,1,2,10,100,500,1073]:
  try: out[objname][str(i)]={'parent':obj.get_bone_parent(i),'children':obj.get_bone_children(i)}
  except Exception as e: out[objname][str(i)]={'err':str(e)}
try: out['sm_skeleton_same']=str(sm.get_editor_property('skeleton')==sk)
except: pass
open('D:/TLOU2_UE5_8_Codex/Exports/probe_bone_verify.json','w').write(json.dumps(out,indent=2,default=str))
