import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
source=json.load(open(ROOT+'/Exports/capture_matched_catalog_map_result.json'))
paths=sorted({slot['material'].split('.')[0] for actor in source['actors'] for slot in actor['materials']})
rows=[]
for path in paths:
    material=unreal.load_asset(path)
    row={'material':path,
         'skeletal_mesh':bool(unreal.MaterialEditingLibrary.has_material_usage(material,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)),
         'morph_targets':bool(unreal.MaterialEditingLibrary.has_material_usage(material,unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS))}
    assert row['skeletal_mesh'] and row['morph_targets'],row
    rows.append(row)
out={'pass':len(rows)==24,'material_count':len(rows),'materials':rows,'verification':'freshprocess persistentusageflagread; noassetmutation'}
assert out['pass']
json.dump(out,open(ROOT+'/Exports/final_material_usage_persistent_validation.json','w'),indent=2)
unreal.log('FINAL_MATERIAL_USAGE_PERSISTENT_PASS '+str(len(rows)))
