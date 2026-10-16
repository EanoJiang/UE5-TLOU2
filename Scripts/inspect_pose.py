import unreal, json
sk=unreal.load_asset('/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'); sm=unreal.load_asset('/Game/TLOU2/ExactBody1074/Ellie_Patrol_ExactBody'); pose=sk.get_reference_pose(); d={'pose_class':pose.get_class().get_name() if hasattr(pose,'get_class') else type(pose).__name__, 'pose_dir':[x for x in dir(pose) if not x.startswith('_')]}
for x in d['pose_dir']:
 try:d[x]=str(pose.get_editor_property(x))
 except:pass
# subsystem
sub=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem); d['sub_dir']=[x for x in dir(sub) if not x.startswith('_') and any(k in x.lower() for k in ('bone','skeleton','lod','section','vertex'))]
for x in d['sub_dir']:
 try:d['sub_'+x]=str(getattr(sub,x)(sm,'root'))
 except Exception as e: d['sub_'+x+'_err']=str(e)
open('D:/TLOU2_UE5_8_Codex/Exports/pose_props.json','w').write(json.dumps(d,indent=2,default=str))
