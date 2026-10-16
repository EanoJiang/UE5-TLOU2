import unreal, json, traceback
mesh=unreal.load_asset('/Game/TLOU2/ExactBody1074/Ellie_Patrol_ExactBody'); anim=unreal.load_asset('/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim'); out={}
try:
 path='/Game/TLOU2/Maps/ElliePatrolCatalogSkeletal'; unreal.EditorLevelLibrary.new_level(path)
 actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0)); actor.set_actor_label('Ellie_Patrol_ExactBody_1074Skeleton'); comp=actor.skeletal_mesh_component; comp.set_editor_property('skeletal_mesh',mesh)
 if anim:
  comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
  data=comp.get_editor_property('animation_data'); data.set_editor_property('anim_to_play',anim); data.set_editor_property('saved_looping',True); data.set_editor_property('saved_playing',True); data.set_editor_property('saved_position',0.0); data.set_editor_property('saved_play_rate',1.0); comp.set_editor_property('animation_data',data); comp.set_update_animation_in_editor(True); comp.play(True)
 # backdrop
 plane=unreal.load_asset('/Engine/BasicShapes/Plane'); mat=unreal.load_asset('/Game/TLOU2/Materials/M_CapturedFrame')
 if plane:
  bg=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(220,0,120),unreal.Rotator(0,90,0)); bg.set_actor_label('Captured_Frame_Backdrop'); bg.static_mesh_component.set_editor_property('static_mesh',plane); bg.set_actor_scale3d(unreal.Vector(2.8,2.0,1.0));
  if mat:bg.static_mesh_component.set_material(0,mat)
 dl=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(150,-250,250),unreal.Rotator(-35,-25,0)); dl.set_actor_label('Catalog_Directional_Light'); dl.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity',8.0)
 pl=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight,unreal.Vector(-150,-100,180),unreal.Rotator(0,0,0)); pl.set_actor_label('Catalog_Fill_Light'); pl.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity',1200.0)
 cam=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(260,-520,160),unreal.Rotator(-8,27,0)); cam.set_actor_label('Catalog_Camera')
 unreal.EditorLevelLibrary.save_current_level(); out={'level':path,'mesh':mesh.get_path_name() if mesh else None,'anim':anim.get_path_name() if anim else None}
except Exception as e:out={'error':repr(e),'tb':traceback.format_exc()}
open('D:/TLOU2_UE5_8_Codex/Exports/skeletal_catalog_map_result.json','w').write(json.dumps(out,indent=2)); unreal.log('SKELETAL_MAP_DONE')
