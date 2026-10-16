import unreal
ROOT=r'D:/TLOU2_UE5_8_Codex'; FBX=ROOT+'/Exports/Ellie_Patrol_ExactBody.fbx'; DEST='/Game/TLOU2/ExactSkeletal'
at=unreal.AssetToolsHelpers.get_asset_tools(); task=unreal.AssetImportTask(); task.filename=FBX; task.destination_path=DEST; task.automated=True; task.replace_existing=True; task.save=True
ui=unreal.FbxImportUI(); ui.set_editor_property('import_mesh',True); ui.set_editor_property('import_as_skeletal',True); ui.set_editor_property('import_animations',False); ui.set_editor_property('import_materials',False); ui.set_editor_property('import_textures',False); task.options=ui
at.import_asset_tasks([task]); unreal.log('EXACT_BODY_SKELETAL_IMPORTED '+str(task.imported_object_paths))
