import unreal, json
root='/Game/TLOU2/Pruned1074'
out='D:/TLOU2_UE5_8_Codex/Exports/verify_pruned_ue.json'
rows=[]
for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
    a=unreal.load_asset(p)
    if not a:
        continue
    row={'path':p,'class':a.get_class().get_name()}
    if isinstance(a, unreal.SkeletalMesh):
        sk=a.get_editor_property('skeleton')
        row['skeleton']=sk.get_path_name() if sk else None
        row['bone_count']=len(sk.get_reference_pose().get_bone_names()) if sk else None
        try:
            row['lod_count']=a.get_num_lods()
        except Exception:
            row['lod_count']=None
        try:
            row['materials']=a.get_num_materials()
        except Exception:
            row['materials']=None
    rows.append(row)
with open(out,'w') as f:
    json.dump(rows,f,indent=2)
unreal.log('VERIFY_PRUNED_UE '+str(rows))
