import unreal, json
unreal.EditorLevelLibrary.load_level('/Game/TLOU2/Maps/ElliePatrolCatalogUI')
rows=[]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    rows.append({'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_name()})
open('D:/TLOU2_UE5_8_Codex/Exports/catalog_ui_actor_inspection.json','w').write(json.dumps(rows,indent=2))
unreal.log('CATALOG_UI_ACTORS '+json.dumps(rows))
