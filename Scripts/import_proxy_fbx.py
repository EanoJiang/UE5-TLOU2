import unreal, os
root=r"D:/TLOU2_UE5_8_Codex"
fbx=root+"/Exports/Ellie_Patrol_Proxy.fbx"
at=unreal.AssetToolsHelpers.get_asset_tools(); task=unreal.AssetImportTask(); task.filename=fbx; task.destination_path='/Game/TLOU2/Proxy'; task.automated=True; task.replace_existing=True; task.save=True
ui=unreal.FbxImportUI(); ui.set_editor_property('import_mesh',True); ui.set_editor_property('import_as_skeletal',True); ui.set_editor_property('import_animations',True); ui.set_editor_property('import_materials',True); ui.set_editor_property('import_textures',False); task.options=ui
at.import_asset_tasks([task]); unreal.log('IMPORTED_PROXY_FBX'); unreal.log(str(task.imported_object_paths))
