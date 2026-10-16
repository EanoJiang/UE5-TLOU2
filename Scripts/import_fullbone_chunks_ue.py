import unreal, json, os, traceback
ROOT='D:/TLOU2_UE5_8_Codex'; FBX_DIR=ROOT+'/Exports/FullBonePruned'; OUT=ROOT+'/Exports/import_fullbone_chunks_result.json'; SK='/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'
sk=unreal.load_asset(SK); at=unreal.AssetToolsHelpers.get_asset_tools(); result={'skeleton':SK,'chunks':[]}
for filename in sorted(os.listdir(FBX_DIR)):
    if not filename.lower().endswith('.fbx'): continue
    chunk=os.path.splitext(filename)[0].replace('Ellie_Patrol_','').replace('_Pruned',''); dest='/Game/TLOU2/FullBone1074/'+chunk
    task=unreal.AssetImportTask(); task.filename=os.path.join(FBX_DIR,filename).replace('\\','/'); task.destination_path=dest; task.automated=True; task.replace_existing=True; task.save=True
    ui=unreal.FbxImportUI(); ui.set_editor_property('import_mesh',True); ui.set_editor_property('import_as_skeletal',True); ui.set_editor_property('import_animations',False); ui.set_editor_property('import_materials',False); ui.set_editor_property('import_textures',False); ui.set_editor_property('create_physics_asset',False); ui.set_editor_property('skeleton',sk); task.options=ui
    row={'file':filename,'destination':dest}
    try:
        at.import_asset_tasks([task]); row['paths']=list(task.imported_object_paths)
    except Exception as e:
        row['error']=repr(e); row['traceback']=traceback.format_exc()
    result['chunks'].append(row); unreal.log('FULLBONE_IMPORT %s paths=%s'%(chunk,row.get('paths',[])))
with open(OUT,'w') as f: json.dump(result,f,indent=2)
unreal.log('FULLBONE_IMPORT_DONE '+OUT)
