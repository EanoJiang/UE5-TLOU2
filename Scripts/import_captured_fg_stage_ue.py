"""Import the source-confirmed FG33 stand and replace only stage actors."""
import unreal,json,os
ROOT='D:/TLOU2_UE5_8_Codex'
doc=json.load(open(ROOT+'/Exports/capture_fg_stage_manifest.json'))
DEST='/Game/TLOU2/CaptureMatched1152/FGStage'
at=unreal.AssetToolsHelpers.get_asset_tools()
task=unreal.AssetImportTask();task.filename=doc['exports']['fbx'];task.destination_path=DEST+'/Meshes';task.automated=True;task.replace_existing=True;task.save=True
ui=unreal.FbxImportUI();ui.set_editor_property('import_mesh',True);ui.set_editor_property('import_as_skeletal',False);ui.set_editor_property('import_animations',False);ui.set_editor_property('import_materials',False);ui.set_editor_property('import_textures',False)
ui.get_editor_property('static_mesh_import_data').set_editor_property('combine_meshes',False)
ui.get_editor_property('static_mesh_import_data').set_editor_property('auto_generate_collision',False)
task.options=ui;at.import_asset_tasks([task])
meshes=[unreal.load_asset(path) for path in task.imported_object_paths]
meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
assert len(meshes)==33,task.imported_object_paths
path=ROOT+'/Scripts/import_decoded_materials_ue.py'
ns={'__name__':'captured_fg_materials'}
exec(compile(open(path).read().split('textures = import_textures()')[0],path,'exec'),ns)
ns['SRC']=ROOT+'/Exports/CapturedFGStage/TexturesDecoded';ns['TEX_DEST']=DEST+'/Textures';ns['MAT_DEST']=DEST+'/Materials'
maps=doc['material_maps']
ns['COLOR']={k:v[0] for k,v in maps.items() if v[0]};ns['NORMAL']={k:v[1] for k,v in maps.items() if v[1]}
ns['AO']={k:v[3] for k,v in maps.items() if v[3]};ns['OPACITY']={k:v[4] for k,v in maps.items() if v[4]}
textures=ns['import_textures']();materials={}
for key,values in maps.items():
    mat=ns['make_material'](key,textures)
    for stem,property,label in [(values[2],unreal.MaterialProperty.MP_ROUGHNESS,'FG_Roughness'),(values[5],unreal.MaterialProperty.MP_METALLIC,'FG_Metallic')]:
        if not stem:continue
        tex=textures[stem.lower()];tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,-800,900)
        node.set_editor_property('texture',tex);node.set_editor_property('parameter_name',label);node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        unreal.MaterialEditingLibrary.connect_material_property(node,'R',property)
    if values[4]:
        # Original depth prepass supplies the cutout. Preserve both the
        # separate mask R channel and its camera-distance threshold.
        mat.set_editor_property('opacity_mask_clip_value',.5)
        k=.6 if 'moss' in key else .3
        mel=unreal.MaterialEditingLibrary
        def expression(cls,x,y):return mel.create_material_expression(mat,cls,x,y)
        mask=expression(unreal.MaterialExpressionTextureSampleParameter2D,-1200,1400)
        mask.set_editor_property('texture',textures[values[4].lower()]);mask.set_editor_property('parameter_name','FG_DepthOpacity')
        mask.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        position=expression(unreal.MaterialExpressionWorldPosition,-1200,1600)
        camera=expression(unreal.MaterialExpressionCameraPositionWS,-1200,1750)
        distance=expression(unreal.MaterialExpressionDistance,-1000,1600)
        meters=expression(unreal.MaterialExpressionDivide,-800,1600);meters.set_editor_property('const_b',100.)
        square_root=expression(unreal.MaterialExpressionSquareRoot,-600,1600)
        factor=expression(unreal.MaterialExpressionMultiply,-400,1600);factor.set_editor_property('const_b',k)
        denominator=expression(unreal.MaterialExpressionMax,-200,1600);denominator.set_editor_property('const_b',1.)
        result=expression(unreal.MaterialExpressionMultiply,0,1400)
        for src,output,dst,input in [(position,'',distance,'A'),(camera,'',distance,'B'),(distance,'',meters,'A'),
                                    (meters,'',square_root,''),(square_root,'',factor,'A'),(factor,'',denominator,'A'),
                                    (mask,'R',result,'A'),(denominator,'',result,'B')]:
            assert mel.connect_material_expressions(src,output,dst,input),(key,dst.get_name(),input)
        assert mel.connect_material_property(result,'',unreal.MaterialProperty.MP_OPACITY_MASK)
    if key in ['ped-gym-floor-lines','pedt-objects-icicles-a']:
        node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-250,1200)
        color=unreal.LinearColor(.75,.75,.7,1) if key=='ped-gym-floor-lines' else unreal.LinearColor(.75,.85,.88,1)
        node.set_editor_property('constant',color);unreal.MaterialEditingLibrary.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
    materials[key]=mat
# This editor module loads after commandlet subsystem startup. Its stateless
# mesh-build functions also work on an explicitly constructed subsystem.
sm_sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) or unreal.StaticMeshEditorSubsystem()
for mesh in meshes:
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
        name=str(slot.get_editor_property('material_slot_name'));key=name[5:] if name.startswith('M_FG_') else name[5:] if name.startswith('M_ND_') else name
        assert key in materials,(mesh.get_name(),name)
        mesh.set_material(i,materials[key])
    settings=sm_sub.get_lod_build_settings(mesh,0)
    settings.set_editor_property('use_full_precision_u_vs',True);settings.set_editor_property('use_high_precision_tangent_basis',True)
    sm_sub.set_lod_build_settings(mesh,0,settings);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
MAP='/Game/TLOU2/Maps/ElliePatrolCaptureMatched'
unreal.EditorLevelLibrary.load_level(MAP)
actors=unreal.EditorLevelLibrary.get_all_level_actors()
def character_signature():
    return {a.get_actor_label():str(a.get_actor_transform()) for a in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(a,unreal.SkeletalMeshActor)}
before=character_signature();removed=[]
for actor in actors:
    if actor.get_actor_label().startswith(('Extracted_Stage_','Captured_FG_Stage_')):
        removed.append(actor.get_actor_label());unreal.EditorLevelLibrary.destroy_actor(actor)
stage=[]
for mesh in sorted(meshes,key=lambda m:m.get_name()):
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0),unreal.Rotator(pitch=0,yaw=0,roll=0))
    actor.set_actor_label('Captured_FG_Stage_'+mesh.get_name())
    comp=actor.static_mesh_component;comp.set_editor_property('static_mesh',mesh);comp.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    actor.set_actor_scale3d(unreal.Vector(1,1,1))
    stage.append({'mesh':mesh.get_path_name(),'actor':actor.get_path_name(),'world_baked':True,'actor_scale':1})
assert before==character_signature(),'characterworldtransforms changed'
unreal.EditorLevelLibrary.save_current_level()
out={'pass':True,'map':MAP,'stage_actor_count':len(stage),'imported_meshes':[m.get_path_name() for m in meshes],
     'stage':stage,'materials':{k:v.get_path_name() for k,v in materials.items()},'textures_imported':len(textures),
     'character_transforms_unchanged':True,'removed_old_stage_actors':removed,
     'scope':'33actualFGworldposedstaticmeshes; lighting/exposure/camera/characters preserved. Pixelshaderlayering remains portablePBR.'}
json.dump(out,open(ROOT+'/Exports/import_captured_fg_stage_result.json','w'),indent=2)
mapreport=json.load(open(ROOT+'/Exports/capture_matched_catalog_map_result.json'))
mapreport['stage']=stage;mapreport['stage_policy']='OriginalFG33 skin+instanceworldbaked;actoridentity;previouscompositesuperseded'
json.dump(mapreport,open(ROOT+'/Exports/capture_matched_catalog_map_result.json','w'),indent=2)
unreal.log('CAPTURED_FG_STAGE_IMPORTED '+json.dumps({'stage_actors':len(stage),'materials':len(materials),'textures':len(textures),'character_unchanged':True}))
