import unreal,json,traceback
FBX='D:/TLOU2_UE5_8_Codex/Exports/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_AnimOnly2.fbx'; DEST='/Game/TLOU2/RawRootCandidates/AnimOnly2'
at=unreal.AssetToolsHelpers.get_asset_tools();t=unreal.AssetImportTask();t.filename=FBX;t.destination_path=DEST;t.automated=True;t.replace_existing=True;t.save=True
ui=unreal.FbxImportUI();ui.set_editor_property('import_mesh',False);ui.set_editor_property('import_as_skeletal',True);ui.set_editor_property('import_animations',True);ui.set_editor_property('import_materials',False);ui.set_editor_property('import_textures',False);ui.set_editor_property('create_physics_asset',False)
sk=unreal.load_asset('/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton');ui.set_editor_property('skeleton',sk);t.options=ui
try:at.import_asset_tasks([t]);out={'paths':list(t.imported_object_paths)}
except Exception as e:out={'exc':repr(e),'tb':traceback.format_exc()}
open('D:/TLOU2_UE5_8_Codex/Exports/import_raw_root_candidate_animonly2_result.json','w').write(json.dumps(out,indent=2)); unreal.log('RAW_ROOT_ANIMONLY2_DONE')
