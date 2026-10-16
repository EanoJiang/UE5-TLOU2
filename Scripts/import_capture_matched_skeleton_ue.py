import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
t=unreal.AssetImportTask();t.filename=ROOT+'/Exports/Ellie_CaptureMatched1074_SkeletonCarrier.fbx';t.destination_path='/Game/TLOU2/CaptureMatched1074/Skeleton';t.automated=True;t.replace_existing=True;t.save=True
ui=unreal.FbxImportUI();ui.set_editor_property('import_mesh',True);ui.set_editor_property('import_as_skeletal',True);ui.set_editor_property('import_animations',False);ui.set_editor_property('import_materials',False);ui.set_editor_property('import_textures',False);ui.set_editor_property('create_physics_asset',False);t.options=ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
skpath='/Game/TLOU2/CaptureMatched1074/Skeleton/Ellie_CaptureMatched1074_SkeletonCarrier_Skeleton';sk=unreal.load_asset(skpath)
out={'paths':list(t.imported_object_paths),'skeleton':skpath,'bones':len(sk.get_reference_pose().get_bone_names()) if sk else 0}
json.dump(out,open(ROOT+'/Exports/import_capture_matched_skeleton_result.json','w'),indent=2)
if not sk or out['bones']!=1075:raise RuntimeError('correctrest skeleton import failed '+str(out))
unreal.log('CAPTURE_MATCHED_SKELETON '+str(out))
