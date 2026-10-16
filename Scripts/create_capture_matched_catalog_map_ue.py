"""Build a real 3D catalog from corrected skins, original static stage and HUD."""
import unreal,json,math
ROOT='D:/TLOU2_UE5_8_Codex'
MAP='/Game/TLOU2/Maps/ElliePatrolCaptureMatched'
ANIM='/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim'
CHUNKS=list(json.load(open(ROOT+'/Exports/captured_skin_pose_chunk_manifest.json'))['chunks'])
unreal.EditorLevelLibrary.new_level(MAP)
sub=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world=sub.get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',unreal.load_class(None,'/Script/TLOU2Codex.CatalogGameMode'))
anim=unreal.load_asset(ANIM)
assert isinstance(anim,unreal.AnimSequence),ANIM
mats={}
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact',recursive=True):
    a=unreal.load_asset(p)
    if isinstance(a,unreal.MaterialInterface):mats[a.get_name()]=a
out={'map':MAP,'animation':ANIM,'actors':[],'stage':[],'material_slots':0,'material_bindings':0,
     'background':'world black; all character/stage geometry is real3D',
     'morph_policy':'CaptureAffineCorrective=1 only for captured static pose'}
for chunk in CHUNKS:
    path='/Game/TLOU2/CaptureMatched1152/CapturedMeshes/'+chunk+'/Ellie_Patrol_'+chunk+'_Pruned'
    mesh=unreal.load_asset(path)
    assert isinstance(mesh,unreal.SkeletalMesh),path
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
    actor.set_actor_label('Ellie_CaptureMatched_'+chunk)
    actor.set_editor_property('tags',['CaptureAffineCorrective'])
    # Captured skin poses are actor-local. Restore the independently recovered
    # actor presentation transform before using the original world camera.
    actor.set_actor_location(unreal.Vector(-3.2344385733,1.7656933532,.00007932785),False,False)
    actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=4.8182263022,roll=0),False)
    comp=actor.skeletal_mesh_component
    comp.set_editor_property('skeletal_mesh',mesh)
    comp.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    data=comp.get_editor_property('animation_data')
    data.set_editor_property('anim_to_play',anim)
    data.set_editor_property('saved_looping',True)
    data.set_editor_property('saved_playing',True)
    data.set_editor_property('saved_position',0.0)
    data.set_editor_property('saved_play_rate',1.0)
    comp.set_editor_property('animation_data',data)
    comp.set_update_animation_in_editor(True)
    comp.set_morph_target('CaptureAffineCorrective',1.0)
    comp.play(True)
    slots=[]
    for i,slot in enumerate(mesh.get_editor_property('materials')):
        name=str(slot.get_editor_property('material_slot_name'))
        material=mats.get(name)
        out['material_slots']+=1
        if material:
            comp.set_material(i,material)
            out['material_bindings']+=1
        slots.append({'slot':name,'material':material.get_path_name() if material else None})
    out['actors'].append({'chunk':chunk,'mesh':path,'actor':actor.get_path_name(),'materials':slots,'bounds':str(actor.get_actor_bounds(False))})
for path in json.load(open(ROOT+'/Exports/import_extracted_catalog_plinth_result.json'))['imported_mesh_paths']:
    mesh=unreal.load_asset(path)
    assert isinstance(mesh,unreal.StaticMesh),path
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
    actor.set_actor_label('Extracted_Stage_'+mesh.get_name())
    actor.set_actor_scale3d(unreal.Vector(1.22,1.22,1.22))
    comp=actor.static_mesh_component
    comp.set_editor_property('static_mesh',mesh)
    comp.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    out['stage'].append({'mesh':path,'actor':actor.get_path_name(),'capture_presentation_scale':1.22,'source_extraction_scale':.5})
def light(cls,label,location,target,intensity):
    v=unreal.Vector(*location)
    rotation=unreal.MathLibrary.find_look_at_rotation(v,unreal.Vector(*target))
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(cls,v,rotation)
    actor.set_actor_label(label)
    comp=actor.get_components_by_class(unreal.LightComponent)[0]
    comp.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    comp.set_editor_property('intensity',intensity)
    return comp
key=light(unreal.RectLight,'Catalog_Key',(-180,280,280),(0,0,105),6500)
key.set_editor_property('source_width',170.0)
key.set_editor_property('source_height',210.0)
fill=light(unreal.RectLight,'Catalog_Fill',(200,180,160),(0,0,100),3000)
fill.set_editor_property('source_width',180.0)
fill.set_editor_property('source_height',180.0)
rim=light(unreal.RectLight,'Catalog_Rim',(-80,-120,230),(0,0,120),5000)
rim.set_editor_property('source_width',120.0)
rim.set_editor_property('source_height',180.0)
pp=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(0,0,0),unreal.Rotator(0,0,0))
pp.set_actor_label('Catalog_Exposure')
pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_method',True)
settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
settings.set_editor_property('override_auto_exposure_bias',True)
settings.set_editor_property('auto_exposure_bias',-9.0)
settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False)
settings.set_editor_property('override_motion_blur_amount',True)
settings.set_editor_property('motion_blur_amount',0.0)
settings.set_editor_property('override_bloom_intensity',True)
settings.set_editor_property('bloom_intensity',0.0)
pp.set_editor_property('settings',settings)
location=unreal.Vector(0,300,115)
target=location+unreal.Vector(.0000026097,-.983470887,-.181064765)*300
rotation=unreal.MathLibrary.find_look_at_rotation(location,target)
cam=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor,location,rotation)
cam.set_actor_label('CatalogCamera')
cam.set_editor_property('tags',['CatalogCamera'])
cam.camera_component.set_editor_property('field_of_view',79.9908974)
out['camera']={'location_cm':[location.x,location.y,location.z],
               'rotation_degrees':[rotation.pitch,rotation.yaw,rotation.roll],'fov_degrees':79.9908974,
               'provenance':'original captured per-view projection and camera basis, world gameYup converted toUE Zup'}
unreal.EditorLevelLibrary.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
json.dump(out,open(ROOT+'/Exports/capture_matched_catalog_map_result.json','w'),indent=2)
unreal.log('CAPTURE_MATCHED_CATALOG_MAP '+json.dumps(out))
