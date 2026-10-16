import unreal,json
all={}
for mapn in ['/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial','/Game/TLOU2/Maps/ElliePatrolCatalogSkeletal']:
 unreal.EditorLevelLibrary.load_level(mapn);rows=[]
 for a in unreal.EditorLevelLibrary.get_all_level_actors():
  if isinstance(a,unreal.SkeletalMeshActor):
   c=a.skeletal_mesh_component; d=c.get_editor_property('animation_data');
   rows.append({'label':a.get_actor_label(),'mode':str(c.get_editor_property('animation_mode')),'anim_to_play':str(d.get_editor_property('anim_to_play')),'saved_playing':str(d.get_editor_property('saved_playing')),'saved_position':str(d.get_editor_property('saved_position'))})
 all[mapn]=rows
open('D:/TLOU2_UE5_8_Codex/Exports/map_anim2.json','w').write(json.dumps(all,indent=2,default=str))
