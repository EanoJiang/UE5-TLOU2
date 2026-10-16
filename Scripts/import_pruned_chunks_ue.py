import unreal, json, os, traceback

ROOT = 'D:/TLOU2_UE5_8_Codex'
OUT = ROOT + '/Exports/import_pruned_chunks_result.json'
FBX_DIR = ROOT + '/Exports/PrunedArmature'
SKELETON_PATH = '/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'

sk = unreal.load_asset(SKELETON_PATH)
result = {'skeleton': SKELETON_PATH, 'chunks': []}
at = unreal.AssetToolsHelpers.get_asset_tools()
manifest_name={'CaptureMatchedChunks':'capture_matched_chunk_manifest.json','CapturedSkinPoseChunks':'captured_skin_pose_chunk_manifest.json'}.get(os.path.basename(FBX_DIR))
if manifest_name:
    authoritative=json.load(open(ROOT+'/Exports/'+manifest_name))
    filenames=sorted(os.path.basename(row['fbx']) for row in authoritative['chunks'].values())
else:
    filenames=sorted(os.listdir(FBX_DIR))
for filename in filenames:
    if not filename.lower().endswith('.fbx'):
        continue
    chunk = os.path.splitext(filename)[0].replace('Ellie_Patrol_', '').replace('_Pruned', '')
    dest = '/Game/TLOU2/Pruned1074/' + chunk
    task = unreal.AssetImportTask()
    task.filename = os.path.join(FBX_DIR, filename).replace('\\', '/')
    task.destination_path = dest
    task.automated = True
    task.replace_existing = True
    task.save = True
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', True)
    ui.set_editor_property('import_as_skeletal', True)
    ui.set_editor_property('import_animations', False)
    ui.set_editor_property('import_materials', False)
    ui.set_editor_property('import_textures', False)
    ui.set_editor_property('create_physics_asset', False)
    if sk:
        ui.set_editor_property('skeleton', sk)
    task.options = ui
    row = {'file': filename, 'destination': dest}
    try:
        at.import_asset_tasks([task])
        # AssetImportTask exposes imported_object_paths in UE 5.8; it does not
        # expose an ``errors`` property.  Keep the result machine-readable and
        # leave importer diagnostics in the Unreal log.
        row['paths'] = list(task.imported_object_paths)
    except Exception as e:
        row['error'] = repr(e)
        row['traceback'] = traceback.format_exc()
    result['chunks'].append(row)
    unreal.log('PRUNED_IMPORT %s paths=%s' % (chunk, row.get('paths', [])))

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)
unreal.log('PRUNED_IMPORT_DONE ' + OUT)
