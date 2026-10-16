import unreal, json, os, traceback

ROOT = 'D:/TLOU2_UE5_8_Codex'
MAP = '/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial'
CHUNKS = [
    '/Game/TLOU2/Pruned1074/body_clothing/Ellie_Patrol_body_clothing_Pruned',
    '/Game/TLOU2/Pruned1074/head_face/Ellie_Patrol_head_face_Pruned',
    '/Game/TLOU2/Pruned1074/hair/Ellie_Patrol_hair_Pruned',
    '/Game/TLOU2/Pruned1074/backpack/Ellie_Patrol_backpack_Pruned',
    '/Game/TLOU2/Pruned1074/accessories/Ellie_Patrol_accessories_Pruned',
]
ANIM = '/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim'
OUT = ROOT + '/Exports/chunked_skeletal_map_result.json'
out = {'map': MAP, 'actors': [], 'material_slots': 0, 'material_bindings': 0}
try:
    unreal.EditorLevelLibrary.new_level(MAP)
    anim = unreal.load_asset(ANIM)
    mats = {}
    for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact', recursive=True):
        a = unreal.load_asset(p)
        if a and a.get_name().startswith('M_ND_'):
            mats[a.get_name()] = a
    for p in CHUNKS:
        sm = unreal.load_asset(p)
        if not isinstance(sm, unreal.SkeletalMesh):
            continue
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        actor.set_actor_label('Ellie_Patrol_' + sm.get_name())
        comp = actor.skeletal_mesh_component
        comp.set_editor_property('skeletal_mesh', sm)
        if anim:
            comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            # UE 5.8's set_animation() updates the preview but can leave
            # SingleAnimationPlayData.anim_to_play unset on disk.  Write the
            # struct explicitly so the map remains animated after reload.
            data = comp.get_editor_property('animation_data')
            data.set_editor_property('anim_to_play', anim)
            data.set_editor_property('saved_looping', True)
            data.set_editor_property('saved_playing', True)
            data.set_editor_property('saved_position', 0.0)
            data.set_editor_property('saved_play_rate', 1.0)
            comp.set_editor_property('animation_data', data)
            comp.set_update_animation_in_editor(True)
            comp.play(True)
        bound = 0
        try:
            for i, slot in enumerate(sm.get_editor_property('materials')):
                out['material_slots'] += 1
                slot_name = str(slot.get_editor_property('material_slot_name'))
                key = slot_name if slot_name.startswith('M_ND_') else ''
                mat = mats.get(key)
                if mat:
                    comp.set_material(i, mat); bound += 1; out['material_bindings'] += 1
        except Exception:
            pass
        out['actors'].append({'mesh': p, 'actor': actor.get_path_name(), 'bound_materials': bound})
    plane = unreal.load_asset('/Engine/BasicShapes/Plane')
    mat = unreal.load_asset('/Game/TLOU2/Materials/M_CapturedFrame')
    if plane:
        bg = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(220, 0, 120), unreal.Rotator(0, 90, 0))
        bg.set_actor_label('Captured_Frame_Backdrop')
        bg.static_mesh_component.set_editor_property('static_mesh', plane)
        bg.set_actor_scale3d(unreal.Vector(2.8, 2.0, 1.0))
        if mat: bg.static_mesh_component.set_material(0, mat)
    dl = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(150, -250, 250), unreal.Rotator(-35, -25, 0)); dl.set_actor_label('Catalog_Directional_Light')
    dl.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity', 8.0)
    pl = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-150, -100, 180), unreal.Rotator(0, 0, 0)); pl.set_actor_label('Catalog_Fill_Light')
    pl.get_components_by_class(unreal.LightComponent)[0].set_editor_property('intensity', 1200.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(260, -520, 160), unreal.Rotator(-8, 27, 0)); cam.set_actor_label('Catalog_Camera')
    unreal.EditorLevelLibrary.save_current_level()
except Exception as e:
    out['error'] = repr(e); out['traceback'] = traceback.format_exc()
json.dump(out, open(OUT, 'w', encoding='utf-8'), indent=2)
unreal.log('CHUNKED_SKELETAL_MAP_DONE ' + json.dumps(out))
