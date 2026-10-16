import unreal,json
MAP='/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate'; unreal.EditorLevelLibrary.load_level(MAP); rows=[]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
 if isinstance(a,unreal.SkeletalMeshActor) and 'RawRootCandidate_Ellie' in a.get_actor_label():
  d=a.skeletal_mesh_component.get_editor_property('animation_data');rows.append({'label':a.get_actor_label(),'anim':str(d.get_editor_property('anim_to_play')),'mode':str(a.skeletal_mesh_component.get_editor_property('animation_mode')),'playing':str(d.get_editor_property('saved_playing'))})
open('D:/TLOU2_UE5_8_Codex/Exports/map_anim_set_reload.json','w').write(json.dumps(rows,indent=2,default=str))
