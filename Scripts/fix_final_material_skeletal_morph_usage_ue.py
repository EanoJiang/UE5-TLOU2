"""UE5.8: explicitly compile the final24 materials for skins and morphs.

Run after the current runtime capture exits. A rendering-enabled commandlet can
populate the target-platform shader cache; a NullRHI run still persists and
verifies usage flags, and the next real-RHI load compiles required permutations.
"""
import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
source=json.load(open(ROOT+'/Exports/capture_matched_catalog_map_result.json'))
paths=sorted({slot['material'].split('.')[0] for actor in source['actors'] for slot in actor['materials']})
assert len(paths)==24,paths
usages=[('skeletal_mesh',unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH),
        ('morph_targets',unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS)]
rows=[]
for path in paths:
    mat=unreal.load_asset(path)
    assert isinstance(mat,unreal.Material),('expected baseMaterial',path)
    before={key:bool(unreal.MaterialEditingLibrary.has_material_usage(mat,usage)) for key,usage in usages}
    # UE5.8 deprecated direct bUsedWith* properties. The public library calls
    # SetBaseMaterialUsage and GetUsageByFlag through HasMaterialUsage.
    for key,usage in usages:
        unreal.MaterialEditingLibrary.set_base_material_usage(mat,usage,True)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    after={key:bool(unreal.MaterialEditingLibrary.has_material_usage(mat,usage)) for key,usage in usages}
    assert all(after.values()),(path,after)
    saved=bool(unreal.EditorAssetLibrary.save_loaded_asset(mat))
    assert saved,('material save failed',path)
    rows.append({'material':path,'before':before,'after':after,'saved':saved})
out={'pass':True,'material_count':len(rows),'materials':rows,
     'source_header_evidence':[
        'Engine/Source/Runtime/Engine/Public/Materials/MaterialInterface.h:76 enumEMaterialUsage; SkeletalMesh and MorphTargets',
        'Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h:196 HasMaterialUsage',
        'Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h:207 SetBaseMaterialUsage'],
     'shader_compile_policy':'Usage flags persisted and recompile requested. RealRHI recapture verifies target-platform shader permutations and absence of missing-usage warnings.'}
json.dump(out,open(ROOT+'/Exports/final_material_usage_fix_result.json','w'),indent=2)
unreal.log('FINAL_MATERIAL_USAGE_FIXED '+json.dumps({'materials':len(rows),'all_skeletal':True,'all_morph':True}))
