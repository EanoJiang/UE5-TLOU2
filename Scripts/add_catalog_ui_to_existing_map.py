import unreal, json
MAP='/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial'
unreal.EditorLevelLibrary.load_level(MAP)
labels={a.get_actor_label() for a in unreal.EditorLevelLibrary.get_all_level_actors()}
out={'map':MAP,'added':[]}
plinth=unreal.load_asset('/Game/TLOU2/Proxy/Catalog_Plinth')
if plinth and 'CatalogUI_Presentation_Plinth' not in labels:
    a=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0)); a.set_actor_label('CatalogUI_Presentation_Plinth'); a.skeletal_mesh_component.set_editor_property('skeletal_mesh',plinth); out['added'].append(a.get_actor_label())
plane=unreal.load_asset('/Engine/BasicShapes/Plane'); mic=unreal.load_asset('/Game/TLOU2/Materials/MI_CatalogInstructionBar')
if plane and mic and 'CatalogUI_CapturedInstructionBar' not in labels:
    a=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,-30,-72),unreal.Rotator(90,0,0)); a.set_actor_label('CatalogUI_CapturedInstructionBar'); a.static_mesh_component.set_editor_property('static_mesh',plane); a.static_mesh_component.set_material(0,mic); a.set_actor_scale3d(unreal.Vector(9.6,0.66,1.0)); out['added'].append(a.get_actor_label())
unreal.EditorLevelLibrary.save_current_level()
open('D:/TLOU2_UE5_8_Codex/Exports/catalog_ui_existing_map_result.json','w').write(json.dumps(out,indent=2))
unreal.log('CATALOG_UI_EXISTING_MAP '+json.dumps(out))
