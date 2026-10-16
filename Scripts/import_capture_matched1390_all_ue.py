ROOT='D:/TLOU2_UE5_8_Codex'
for name in ['import_capture_matched1390_skeleton_ue.py','import_capture_matched1390_chunks_ue.py']:
    path=ROOT+'/Scripts/'+name
    exec(compile(open(path).read(),path,'exec'),{'__name__':'ownedrig_import'})
path=ROOT+'/Scripts/assign_skeletal_materials.py'
code=open(path).read().replace('/Game/TLOU2/Pruned1074','/Game/TLOU2/CaptureMatched1390').replace('assign_skeletal_materials_result.json','assign_capture_matched1390_materials_result.json')
exec(compile(code,path,'exec'),{'__name__':'ownedrig_materials'})
path=ROOT+'/Scripts/import_extracted_catalog_plinth_ue.py'
exec(compile(open(path).read(),path,'exec'),{'__name__':'latest_plinth_import'})
