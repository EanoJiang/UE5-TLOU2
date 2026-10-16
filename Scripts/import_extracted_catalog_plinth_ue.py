import unreal,json,os
ROOT='D:/TLOU2_UE5_8_Codex'
at=unreal.AssetToolsHelpers.get_asset_tools();task=unreal.AssetImportTask();task.filename=ROOT+'/Exports/Catalog_Extracted_WetPlinth.fbx';task.destination_path='/Game/TLOU2/CaptureMatched1074/PlinthMeshes';task.automated=True;task.replace_existing=True;task.save=True
ui=unreal.FbxImportUI();ui.set_editor_property('import_mesh',True);ui.set_editor_property('import_as_skeletal',False);ui.set_editor_property('import_animations',False);ui.set_editor_property('import_materials',False);ui.set_editor_property('import_textures',False);task.options=ui;at.import_asset_tasks([task])
code=open(ROOT+'/Scripts/import_decoded_materials_ue.py').read().split('textures = import_textures()')[0];ns={'__name__':'plinth_material_import'};exec(compile(code,ROOT+'/Scripts/import_decoded_materials_ue.py','exec'),ns)
ns['SRC']=ROOT+'/Exports/PlinthTexturesDecoded';ns['TEX_DEST']='/Game/TLOU2/CaptureMatched1074/PlinthTextures';ns['MAT_DEST']='/Game/TLOU2/CaptureMatched1074/PlinthMaterials';ns['MESH_DEST']='/Game/TLOU2/CaptureMatched1074/PlinthMeshes'
maps=json.load(open(ROOT+'/Exports/extracted_catalog_plinth_manifest.json'))['material_maps'];ns['COLOR']={k:v[0] for k,v in maps.items()};ns['NORMAL']={k:v[1] for k,v in maps.items()};ns['AO']={};ns['OPACITY']={k:v[2] for k,v in maps.items() if v[2]}
textures=ns['import_textures']();materials={k:ns['make_material'](k,textures) for k in maps};counts=ns['assign_materials'](materials)
out={'imported_mesh_paths':list(task.imported_object_paths),'textures':len(textures),'materials':list(materials),'assigned_meshes_slots':counts}
json.dump(out,open(ROOT+'/Exports/import_extracted_catalog_plinth_result.json','w'),indent=2);unreal.log('IMPORTED_EXTRACTED_PLINTH '+str(out))
