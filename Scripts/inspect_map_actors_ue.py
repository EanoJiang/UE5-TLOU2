import unreal, json, sys
allout={}
for path in ['/Game/TLOU2/Maps/ElliePatrolCatalogSkeletal','/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial','/Game/TLOU2/Maps/ElliePatrolCatalogUI_Final']:
    unreal.EditorLevelLibrary.load_level(path)
    allout[path]=[{'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_name()} for a in unreal.EditorLevelLibrary.get_all_level_actors()]
open('D:/TLOU2_UE5_8_Codex/Exports/map_actor_inspection.json','w').write(json.dumps(allout,indent=2))
