import unreal,json
paths=['/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim','/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim']
out={}
for p in paths:
 a=unreal.load_asset(p); d={'path':p,'class':str(a.get_class()) if a else None}
 d['dir']=[x for x in dir(a) if not x.startswith('_')] if a else []
 d['props']={}
 for x in d['dir']:
  try:
   v=a.get_editor_property(x)
   if isinstance(v,(str,int,float,bool,type(None))):d['props'][x]=v
   elif isinstance(v,(list,tuple)):d['props'][x]=str(v)[:300]
  except: pass
 out[p]=d
open('D:/TLOU2_UE5_8_Codex/Exports/anim_api_inspect.json','w').write(json.dumps(out,indent=2,default=str))
print(json.dumps(out,indent=2,default=str))
