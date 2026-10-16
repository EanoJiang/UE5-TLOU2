import unreal, json

root = '/Game/TLOU2/Pruned1074'
out = {'assets': [], 'count': 0, 'shared_probe_count': 1075}
for p in sorted(unreal.EditorAssetLibrary.list_assets(root, recursive=True)):
    a = unreal.load_asset(p)
    if not isinstance(a, unreal.SkeletalMesh):
        continue
    sk = a.get_editor_property('skeleton')
    bones = len(sk.get_reference_pose().get_bone_names()) if sk else 0
    out['assets'].append({'path': p, 'bones': bones, 'skeleton': sk.get_path_name() if sk else None})
out['count'] = len(out['assets'])
json.dump(out, open('D:/TLOU2_UE5_8_Codex/Exports/pruned_chunks_verify.json', 'w', encoding='utf-8'), indent=2)
unreal.log('PRUNED_CHUNKS_VERIFY ' + json.dumps(out))
