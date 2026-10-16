import unreal, json
paths=['/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe','/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton','/Game/TLOU2/ExactBody1074/Ellie_Patrol_ExactBody']
out={}
for p in paths:
 a=unreal.load_asset(p); d={'class':a.get_class().get_name() if a else None}
 if a:
  d['dir']=[x for x in dir(a) if not x.startswith('_') and any(k in x.lower() for k in ('bone','skeleton','reference','lod','vertex','uv','section','influ'))]
  for attr in d['dir']:
   try:
    v=a.get_editor_property(attr); d[attr]=str(v)
   except Exception as e: pass
  if isinstance(a,unreal.SkeletalMesh):
   try:d['ref_skeleton']=str(a.get_editor_property('ref_skeleton'))
   except Exception as e:d['ref_skeleton_error']=str(e)
   try:d['skeleton']=str(a.get_editor_property('skeleton'))
   except Exception as e:d['skeleton_error']=str(e)
 out[p]=d
open('D:/TLOU2_UE5_8_Codex/Exports/probe_asset_props.json','w').write(json.dumps(out,indent=2))
