import unreal, os, json, traceback

ROOT = 'D:/TLOU2_UE5_8_Codex'
MAP = '/Game/TLOU2/Maps/ElliePatrolCatalogUI_Final'
CHUNKS = [
    '/Game/TLOU2/Pruned1074/body_clothing/Ellie_Patrol_body_clothing_Pruned',
    '/Game/TLOU2/Pruned1074/head_face/Ellie_Patrol_head_face_Pruned',
    '/Game/TLOU2/Pruned1074/hair/Ellie_Patrol_hair_Pruned',
    '/Game/TLOU2/Pruned1074/backpack/Ellie_Patrol_backpack_Pruned',
    '/Game/TLOU2/Pruned1074/accessories/Ellie_Patrol_accessories_Pruned',
]
ANIM = '/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim'
OUT = ROOT + '/Exports/catalog_ui_map_result.json'

def make_bar_material():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    png = ROOT + '/Content/TLOU2/Reference/catalog_instruction_bar.png'
    task = unreal.AssetImportTask(); task.filename = png; task.destination_path = '/Game/TLOU2/Reference'; task.destination_name = 'T_CatalogInstructionBar'; task.automated = True; task.replace_existing = True; task.save = True
    at.import_asset_tasks([task])
    tex = unreal.load_asset('/Game/TLOU2/Reference/T_CatalogInstructionBar')
    # Reuse the already-created unlit/two-sided M_CapturedFrame graph and make a
    # material instance with the cropped instruction texture. Material creation
    # through MaterialFactoryNew is editor-only in some UE 5.8 commandlet builds.
    parent = unreal.load_asset('/Game/TLOU2/Materials/M_CapturedFrame')
    mic = unreal.load_asset('/Game/TLOU2/Materials/MI_CatalogInstructionBar')
    if not mic and parent:
        mic = at.create_asset('MI_CatalogInstructionBar', '/Game/TLOU2/Materials', unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if mic and parent:
        mic.set_editor_property('parent', parent)
        if tex:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mic, 'CapturedFrame', tex)
        unreal.EditorAssetLibrary.save_loaded_asset(mic)
    return mic

out = {'map': MAP, 'actors': [], 'instruction_bar': None, 'errors': []}
try:
    unreal.EditorLevelLibrary.new_level(MAP)
    anim = unreal.load_asset(ANIM)
    # Outfit chunks share Probe1074 and are kept at one origin for an editable catalog view.
    for p in CHUNKS:
        sm = unreal.load_asset(p)
        if not isinstance(sm, unreal.SkeletalMesh):
            out['errors'].append('missing '+p); continue
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
        actor.set_actor_label('CatalogUI_' + sm.get_name())
        comp = actor.skeletal_mesh_component; comp.set_editor_property('skeletal_mesh', sm)
        if anim:
            comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); comp.set_animation(anim); comp.play(True)
        out['actors'].append({'mesh': p, 'actor': actor.get_path_name()})
    # The source capture contains the circular presentation plinth. The proxy is skeletal,
    # so it is displayed as a separate actor to preserve its editable geometry/material.
    plinth = unreal.load_asset('/Game/TLOU2/Proxy/Catalog_Plinth')
    if isinstance(plinth, unreal.SkeletalMesh):
        pa = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
        pa.set_actor_label('CatalogUI_Presentation_Plinth'); pa.skeletal_mesh_component.set_editor_property('skeletal_mesh', plinth)
        out['plinth'] = pa.get_path_name()
    # Add the captured instruction strip as a two-sided unlit plane near the camera.
    bar = make_bar_material()
    plane = unreal.load_asset('/Engine/BasicShapes/Plane')
    if plane and bar:
        ba = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, -30, -72), unreal.Rotator(90,0,0))
        ba.set_actor_label('CatalogUI_CapturedInstructionBar'); ba.static_mesh_component.set_editor_property('static_mesh', plane); ba.static_mesh_component.set_material(0, bar)
        ba.set_actor_scale3d(unreal.Vector(9.6, 0.66, 1.0)); out['instruction_bar'] = ba.get_path_name()
    # Presentation lighting and a camera remain editable in the map.
    dl = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(150,-250,250), unreal.Rotator(-35,-25,0)); dl.set_actor_label('CatalogUI_KeyLight'); dl.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity',8.0)
    pl = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-150,-100,180), unreal.Rotator(0,0,0)); pl.set_actor_label('CatalogUI_FillLight'); pl.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity',1200.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(260,-520,160), unreal.Rotator(-8,27,0)); cam.set_actor_label('CatalogUI_Camera')
    out['camera'] = cam.get_path_name()
    world = unreal.EditorLevelLibrary.get_editor_world()
    save_path = ROOT + '/Content/TLOU2/Maps/ElliePatrolCatalogUI_Final.umap'
    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, save_path)
    out['saved'] = bool(saved)
except Exception as e:
    out['errors'].append(repr(e)); out['traceback'] = traceback.format_exc()
json.dump(out, open(OUT, 'w', encoding='utf8'), indent=2)
unreal.log('CATALOG_UI_MAP_DONE '+json.dumps(out))
