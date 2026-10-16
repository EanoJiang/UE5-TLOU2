import unreal
ROOT=r'D:/TLOU2_UE5_8_Codex'; FBX=ROOT+'/Exports/Ellie_Patrol_Catalog_ExactStatic.fbx'; DEST='/Game/TLOU2/ExactStatic'
at=unreal.AssetToolsHelpers.get_asset_tools(); task=unreal.AssetImportTask(); task.filename=FBX; task.destination_path=DEST; task.automated=True; task.replace_existing=True; task.save=True
ui=unreal.FbxImportUI(); ui.set_editor_property('import_mesh',True); ui.set_editor_property('import_as_skeletal',False); ui.set_editor_property('import_materials',False); ui.set_editor_property('import_textures',False); task.options=ui
at.import_asset_tasks([task]); unreal.log('EXACT_STATIC_IMPORTED '+str(task.imported_object_paths))
unreal.EditorLevelLibrary.new_level('/Game/TLOU2/Maps/ElliePatrolCatalog')
for p in task.imported_object_paths:
    a=unreal.load_asset(p)
    if isinstance(a,unreal.StaticMesh):
        actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0)); actor.set_actor_label('Exact_'+a.get_name()); actor.static_mesh_component.set_editor_property('static_mesh',a)
plane=unreal.load_asset('/Engine/BasicShapes/Plane'); mat=unreal.load_asset('/Game/TLOU2/Materials/M_CapturedFrame')
if plane:
    bg=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(220,0,120),unreal.Rotator(0,90,0)); bg.set_actor_label('Captured_Frame_Backdrop'); bg.static_mesh_component.set_editor_property('static_mesh',plane); bg.set_actor_scale3d(unreal.Vector(2.8,2.0,1.0))
    if mat: bg.static_mesh_component.set_material(0,mat)
unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(150,-250,250),unreal.Rotator(-35,-25,0))
unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight,unreal.Vector(-150,-100,180),unreal.Rotator(0,0,0))
unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(260,-520,160),unreal.Rotator(-8,27,0))
unreal.EditorLevelLibrary.save_current_level(); unreal.EditorAssetLibrary.save_directory(DEST); unreal.log('EXACT_STATIC_LEVEL_SAVED')
