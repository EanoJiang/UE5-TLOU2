import unreal,json,math
from collections import Counter
ROOT='D:/TLOU2_UE5_8_Codex'
MAP='/Game/TLOU2/Maps/ElliePatrolCaptureMatched'
chunks=json.load(open(ROOT+'/Exports/captured_skin_pose_chunk_manifest.json'))['chunks']
unreal.EditorLevelLibrary.load_level(MAP)
actors=unreal.EditorLevelLibrary.get_all_level_actors()
sk=unreal.load_asset('/Game/TLOU2/CaptureMatched1152/Skeleton/Ellie_CaptureMatched1152_SkeletonCarrier_Skeleton')
anim=unreal.load_asset('/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim')
assert len(sk.get_reference_pose().get_bone_names())==1153
assert anim and anim.get_skeleton()==sk
rows=[]
for actor in actors:
    if not isinstance(actor,unreal.SkeletalMeshActor):continue
    comp=actor.skeletal_mesh_component
    mesh=comp.get_editor_property('skeletal_mesh')
    data=comp.get_editor_property('animation_data')
    path=mesh.get_path_name()
    chunk=path.split('/CapturedMeshes/')[1].split('/')[0]
    assert chunk in chunks,('unexpected chunk actor',path)
    assert mesh.get_editor_property('skeleton')==sk,('wrong skeleton',path)
    assert data.get_editor_property('anim_to_play')==anim,('animation not persisted',path)
    assert 'CaptureAffineCorrective' in [str(t) for t in actor.get_editor_property('tags')]
    slots=[]
    for i,slot in enumerate(mesh.get_editor_property('materials')):
        material=comp.get_material(i)
        assert material and material.get_name().startswith('M_ND_'),('missing material',path,i)
        slots.append({'slot':str(slot.get_editor_property('material_slot_name')),'material':material.get_path_name()})
    rows.append({'chunk':chunk,'mesh':path,'materials':slots,'animation_serialized':True,
                 'world_location_cm':str(actor.get_actor_location()),'world_rotation':str(actor.get_actor_rotation())})
assert len(rows)==len(chunks),(len(rows),len(chunks))
assert {r['chunk'] for r in rows}==set(chunks)
camera=next(a for a in actors if isinstance(a,unreal.CameraActor) and 'CatalogCamera' in [str(t) for t in a.get_editor_property('tags')])
fov=camera.camera_component.get_editor_property('field_of_view')
assert abs(fov-79.9908974)<.0001
location=camera.get_actor_location()
assert abs(location.x)<.0001 and abs(location.y-300)<.0001 and abs(location.z-115)<.0001
lights=[a for a in actors if isinstance(a,unreal.Light)]
for light in lights:
    assert light.get_components_by_class(unreal.LightComponent)[0].get_editor_property('mobility')==unreal.ComponentMobility.MOVABLE
stage_manifest=json.load(open(ROOT+'/Exports/capture_fg_stage_manifest.json'))
stage=[a for a in actors if a.get_actor_label().startswith('Captured_FG_Stage_')]
assert len(stage)==stage_manifest['meshes']==33,len(stage)
stage_import=json.load(open(ROOT+'/Exports/import_captured_fg_stage_result.json'))
assert Counter(a.static_mesh_component.static_mesh.get_path_name() for a in stage)==Counter(stage_import['imported_meshes'])
stage_rows=[]
for actor in stage:
    scale=actor.get_actor_scale3d();stage_location=actor.get_actor_location();rotation=actor.get_actor_rotation()
    assert max(abs(scale.x-1),abs(scale.y-1),abs(scale.z-1),abs(stage_location.x),abs(stage_location.y),abs(stage_location.z),abs(rotation.pitch),abs(rotation.yaw),abs(rotation.roll))<.0001
    assert '/CaptureMatched1152/FGStage/Meshes/' in actor.static_mesh_component.static_mesh.get_path_name()
    comp=actor.static_mesh_component;bindings=[]
    for i,slot in enumerate(comp.static_mesh.get_editor_property('static_materials')):
        name=str(slot.get_editor_property('material_slot_name'));key=name[5:] if name.startswith(('M_FG_','M_ND_')) else name
        actual=comp.get_material(i);assert actual and actual.get_path_name()==stage_import['materials'][key]
        bindings.append({'slot':name,'material':actual.get_path_name()})
    stage_rows.append({'mesh':comp.static_mesh.get_path_name(),'actor':actor.get_path_name(),'materials':bindings,'identity_transform':True})
assert not any(a.get_actor_label().startswith('Extracted_Stage_') for a in actors)
assert not any('Backdrop' in a.get_actor_label() or 'Captured_Frame' in a.get_actor_label() for a in actors)
out={'pass':True,'map':MAP,'skeleton_bones_including_export_object':1153,
     'character_actor_count':len(rows),'character_chunks':rows,'stage_actor_count':len(stage),
     'stage_mesh_identity_multiset_matches_import':True,'stage':stage_rows,
     'camera_hfov_degrees':fov,'camera_location_cm':[location.x,location.y,location.z],
     'movable_lights':len(lights),'runtime_morph_policy':'CaptureAffineCorrective actor tag restored by CatalogPawn; captured animation curve can also persist editor deformation'}
json.dump(out,open(ROOT+'/Exports/capture_matched_catalog_map_validation.json','w'),indent=2)
unreal.log('CAPTURE_MATCHED_MAP_VERIFIED '+json.dumps({k:v for k,v in out.items() if k!='character_chunks'}))
