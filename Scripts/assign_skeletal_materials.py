import unreal, json

mats = {}
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact', recursive=True):
    a = unreal.load_asset(p)
    if a and a.get_name().startswith('M_ND_'):
        mats[a.get_name()] = a
out = {'assets': [], 'bound': 0, 'slots': 0}
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Pruned1074', recursive=True):
    sm = unreal.load_asset(p)
    if not isinstance(sm, unreal.SkeletalMesh):
        continue
    arr = sm.get_editor_property('materials')
    bound = 0
    for slot in arr:
        out['slots'] += 1
        name = str(slot.get_editor_property('material_slot_name'))
        mat = mats.get(name)
        if mat:
            try:
                slot.set_editor_property('material_interface', mat)
                bound += 1
            except Exception:
                pass
    try:
        sm.set_editor_property('materials', arr)
        unreal.EditorAssetLibrary.save_loaded_asset(sm)
    except Exception as e:
        out.setdefault('errors', []).append({'asset': p, 'error': repr(e)})
    out['bound'] += bound
    out['assets'].append({'asset': p, 'bound': bound})
json.dump(out, open('D:/TLOU2_UE5_8_Codex/Exports/assign_skeletal_materials_result.json', 'w', encoding='utf-8'), indent=2)
unreal.log('ASSIGN_SKELETAL_MATERIALS ' + json.dumps(out))
