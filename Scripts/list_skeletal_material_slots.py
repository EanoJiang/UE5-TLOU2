import unreal, json

out = {}
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Pruned1074', recursive=True):
    a = unreal.load_asset(p)
    if not isinstance(a, unreal.SkeletalMesh):
        continue
    rows = []
    for s in a.get_editor_property('materials'):
        rows.append({'slot': str(s.get_editor_property('material_slot_name')), 'material': str(s.get_editor_property('material_interface'))})
    out[p] = rows
json.dump(out, open('D:/TLOU2_UE5_8_Codex/Exports/pruned_material_slots.json', 'w', encoding='utf-8'), indent=2)
unreal.log('PRUNED_MATERIAL_SLOTS ' + json.dumps(out))
