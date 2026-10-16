import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
sub=unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
rows=[]
paths=[]
for manifest,folder in [('capture_matched_chunk_manifest.json',''),('captured_skin_pose_chunk_manifest.json','CapturedMeshes/')]:
    for chunk in json.load(open(ROOT+'/Exports/'+manifest))['chunks']:
        paths.append('/Game/TLOU2/CaptureMatched1152/'+folder+chunk+'/Ellie_Patrol_'+chunk+'_Pruned')
for path in paths:
    mesh=unreal.load_asset(path)
    if not isinstance(mesh,unreal.SkeletalMesh):continue
    settings=sub.get_lod_build_settings(mesh,0)
    settings.set_editor_property('bone_influence_limit',12)
    settings.set_editor_property('use_high_precision_skin_weights',True)
    settings.set_editor_property('use_full_precision_u_vs',True)
    settings.set_editor_property('use_high_precision_tangent_basis',True)
    settings.set_editor_property('morph_threshold_position',.000001)
    sub.set_lod_build_settings(mesh,0,settings)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    rows.append({'mesh':path,'bone_influence_limit':12,'skin_weight_precision':'16bit',
                 'uv_precision':'float32','morph_position_threshold_cm':.000001})
json.dump({'meshes':rows},open(ROOT+'/Exports/capture_mesh_precision_report.json','w'),indent=2)
unreal.log('CAPTURE_MESH_PRECISION '+str(len(rows)))
