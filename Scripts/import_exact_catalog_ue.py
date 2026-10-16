import unreal, os

ROOT=r'D:/TLOU2_UE5_8_Codex'
FBX=ROOT+'/Exports/Ellie_Patrol_Catalog_Exact.fbx'
DEST='/Game/TLOU2/Exact'
at=unreal.AssetToolsHelpers.get_asset_tools()
task=unreal.AssetImportTask(); task.filename=FBX; task.destination_path=DEST; task.automated=True; task.replace_existing=True; task.save=True
ui=unreal.FbxImportUI(); ui.set_editor_property('import_mesh',True); ui.set_editor_property('import_as_skeletal',True); ui.set_editor_property('import_animations',False); ui.set_editor_property('import_materials',False); ui.set_editor_property('import_textures',False); task.options=ui
at.import_asset_tasks([task])
unreal.log('EXACT_FBX_IMPORTED '+str(task.imported_object_paths))

def find_asset(paths, cls):
    for p in paths:
        a=unreal.load_asset(p)
        if a and isinstance(a,cls): return a
    return None

sk=find_asset(task.imported_object_paths, unreal.SkeletalMesh)
anim=find_asset(task.imported_object_paths, unreal.AnimationSequence)
if not sk:
    for p in unreal.EditorAssetLibrary.list_assets(DEST,recursive=True):
        a=unreal.load_asset(p)
        if isinstance(a,unreal.SkeletalMesh): sk=a
        if isinstance(a,unreal.AnimationSequence): anim=anim or a

map_path='/Game/TLOU2/Maps/ElliePatrolCatalog'
unreal.EditorLevelLibrary.new_level(map_path)
if sk:
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
    actor.set_actor_label('Ellie_Patrol_Catalog_Exact')
    comp=actor.skeletal_mesh_component; comp.set_editor_property('skeletal_mesh',sk)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); comp.set_animation(anim); comp.play(True)

plane=unreal.load_asset('/Engine/BasicShapes/Plane'); mat=unreal.load_asset('/Game/TLOU2/Materials/M_CapturedFrame')
if plane:
    bg=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(220,0,120),unreal.Rotator(0,90,0))
    bg.set_actor_label('Captured_Frame_Backdrop'); bg.static_mesh_component.set_editor_property('static_mesh',plane); bg.set_actor_scale3d(unreal.Vector(2.8,2.0,1.0))
    if mat: bg.static_mesh_component.set_material(0,mat)

for cls,loc,rot,energy in [(unreal.DirectionalLight,unreal.Vector(150,-250,250),unreal.Rotator(-35,-25,0),8.0),(unreal.PointLight,unreal.Vector(-150,-100,180),unreal.Rotator(0,0,0),1200.0)]:
    l=unreal.EditorLevelLibrary.spawn_actor_from_class(cls,loc,rot); l.set_actor_label('Catalog_Light'); l.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE); l.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity',energy)

cam=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(260,-520,160),unreal.Rotator(-8,27,0)); cam.set_actor_label('Catalog_Camera')
unreal.EditorLevelLibrary.save_current_level(); unreal.EditorAssetLibrary.save_directory(DEST)
unreal.log('EXACT_CATALOG_LEVEL_SAVED '+map_path+' mesh='+str(sk)+' anim='+str(anim))
