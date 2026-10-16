import unreal, json
MAP='/Game/TLOU2/Maps/ElliePatrolCatalogUI'
unreal.EditorLevelLibrary.load_level(MAP)
mic=unreal.load_asset('/Game/TLOU2/Materials/MI_CatalogInstructionBar')
rows=[]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    label=str(a.get_actor_label())
    if label=='CatalogUI_CapturedInstructionBar' and mic:
        a.static_mesh_component.set_material(0,mic); rows.append({'actor':label,'material':mic.get_path_name()})
unreal.EditorLevelLibrary.save_current_level()
out={'map':MAP,'fixed':rows,'material':mic.get_path_name() if mic else None}
open('D:/TLOU2_UE5_8_Codex/Exports/catalog_ui_material_fix.json','w').write(json.dumps(out,indent=2))
unreal.log('CATALOG_UI_MATERIAL_FIX '+json.dumps(out))
