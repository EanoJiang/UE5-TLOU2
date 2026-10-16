import unreal,json
sm=unreal.load_asset('/Game/TLOU2/Pruned1074/body_clothing/Ellie_Patrol_body_clothing_Pruned')
# load map
unreal.EditorLevelLibrary.load_level('/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate')
rows=[]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
 if isinstance(a,unreal.SkeletalMeshActor):
  c=a.skeletal_mesh_component; row={'actor':a.get_actor_label(),'class':a.get_class().get_name(),'dir':[x for x in dir(c) if 'anim' in x.lower() or 'skeletal' in x.lower()]}
  for name in ['get_animation','animation_data','get_editor_property']:
   try:
    if name=='get_animation':v=c.get_animation()
    elif name=='animation_data':v=c.get_editor_property('animation_data')
    else:v=c.get_editor_property('animation_mode')
    row[name]=str(v)
    if name=='animation_data':
     for p in ['anim_to_play','animation','play_rate','b_saved_looping','b_saved_playing']:
      try:row['ad_'+p]=str(v.get_editor_property(p))
      except Exception as e:row['ad_'+p]='ERR '+repr(e)
   except Exception as e:row[name]='ERR '+repr(e)
  rows.append(row)
json.dump(rows,open('D:/TLOU2_UE5_8_Codex/Exports/map_anim_component_probe.json','w'),indent=2,default=str)
print(json.dumps(rows,indent=2,default=str))
