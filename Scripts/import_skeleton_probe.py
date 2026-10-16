import unreal
FBX='D:/TLOU2_UE5_8_Codex/Exports/Ellie_1074_SkeletonProbe.fbx'; DEST='/Game/TLOU2/Probe1074'
asset_tools=unreal.AssetToolsHelpers.get_asset_tools()
t=unreal.AssetImportTask(); t.filename=FBX; t.destination_path=DEST; t.automated=True; t.replace_existing=True; t.save=True
ui=unreal.FbxImportUI(); ui.set_editor_property('import_mesh',True); ui.set_editor_property('import_as_skeletal',True); ui.set_editor_property('import_animations',False); ui.set_editor_property('import_materials',False); ui.set_editor_property('import_textures',False); t.options=ui
unreal.log('PROBE_BEGIN')
asset_tools.import_asset_tasks([t])
unreal.log('PROBE_IMPORTED '+str(t.imported_object_paths))
for p in t.imported_object_paths:
 a=unreal.load_asset(p)
 if a: unreal.log('PROBE_ASSET '+p+' cls='+a.get_class().get_name())
unreal.EditorAssetLibrary.save_directory(DEST); unreal.log('PROBE_END')
