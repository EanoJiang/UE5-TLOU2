import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
skpath='/Game/TLOU2/CaptureMatched1074/Skeleton/Ellie_CaptureMatched1074_SkeletonCarrier_Skeleton';sk=unreal.load_asset(skpath)
t=unreal.AssetImportTask();t.filename=ROOT+'/Exports/Ellie_Original_0FW_AnimationCarrier.fbx';t.destination_path='/Game/TLOU2/CaptureMatched1074/Animations';t.automated=True;t.replace_existing=True;t.save=True
ui=unreal.FbxImportUI();ui.set_editor_property('import_mesh',True);ui.set_editor_property('import_as_skeletal',True);ui.set_editor_property('import_animations',True);ui.set_editor_property('import_materials',False);ui.set_editor_property('import_textures',False);ui.set_editor_property('create_physics_asset',False);ui.set_editor_property('skeleton',sk);t.options=ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);out={'paths':list(t.imported_object_paths),'skeleton':skpath}
for p in t.imported_object_paths:
    a=unreal.load_asset(p)
    if isinstance(a,unreal.AnimSequence):
        a.set_editor_property('enable_root_motion',False)
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        out['animation']=a.get_path_name();out['seconds']=float(a.get_play_length());out['same_skeleton']=a.get_skeleton()==sk
json.dump(out,open(ROOT+'/Exports/import_original_0fw_animation_result.json','w'),indent=2)
if 'animation' not in out:raise RuntimeError('original animation import failed '+str(out))
unreal.log('ORIGINAL_0FW_ANIMATION_IMPORT '+str(out))
