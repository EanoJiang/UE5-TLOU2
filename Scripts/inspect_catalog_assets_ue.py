import unreal, json
rows=[]
for p in ['/Game/TLOU2/Proxy/Catalog_Plinth','/Game/TLOU2/Proxy/Catalog_Plinth_Skeleton','/Game/TLOU2/Proxy/Ellie_Patrol_Backpack']:
    a=unreal.load_asset(p)
    row={'path':p,'class':a.get_class().get_name() if a else None}
    if isinstance(a,unreal.StaticMesh):
        row['bounds_origin']=str(a.get_bounds().origin); row['bounds_box_extent']=str(a.get_bounds().box_extent); row['materials']=[str(x.get_editor_property('material_interface')) for x in a.get_editor_property('static_materials')]
    if isinstance(a,unreal.SkeletalMesh):
        row['bounds_origin']=str(a.get_bounds().origin); row['bounds_box_extent']=str(a.get_bounds().box_extent); row['materials']=[str(x.get_editor_property('material_interface')) for x in a.get_editor_property('materials')]
    rows.append(row)
open('D:/TLOU2_UE5_8_Codex/Exports/catalog_asset_inspection.json','w').write(json.dumps(rows,indent=2))
unreal.log('CATALOG_ASSET_INSPECTION '+json.dumps(rows))
