import bpy,json,os,math
p=r'D:\TLOU2_UE5_8_Codex\Exports\Ellie_1074_RootMotion_AnimationProbe.fbx'; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=p,use_anim=True)
report={'file':p,'objects':[],'actions':[]}
for ob in bpy.data.objects:
 if ob.type=='ARMATURE':
  a=ob.animation_data.action if ob.animation_data else None
  od={'name':ob.name,'bones':len(ob.data.bones),'action':a.name if a else None}
  if a:
   od['frame_range']=list(map(float,a.frame_range)); od['fcurves']=len(a.fcurves); root=[]
   for fc in a.fcurves:
    if fc.data_path in ('location','pose.bones["root"].location'):
     vals=[float(k.co[1]) for k in fc.keyframe_points];
     root.append({'path':fc.data_path,'axis':fc.array_index,'keys':len(vals),'min':min(vals) if vals else None,'max':max(vals) if vals else None,'first':vals[0] if vals else None,'last':vals[-1] if vals else None})
   od['root_motion_curves']=root
  report['objects'].append(od)
json.dump(report,open(r'D:\TLOU2_UE5_8_Codex\Exports\rootmotion_fbx_verification.json','w'),indent=2)
print(json.dumps(report,indent=2))
