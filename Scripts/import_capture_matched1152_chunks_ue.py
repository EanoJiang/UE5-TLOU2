ROOT='D:/TLOU2_UE5_8_Codex'
path=ROOT+'/Scripts/import_capture_matched1390_chunks_ue.py'
code=open(path).read().replace('1390','1152')
exec(compile(code,path,'exec'),{'__name__':'correct_outfit_mesh_import'})
path=ROOT+'/Scripts/assign_skeletal_materials.py'
code=open(path).read().replace('/Game/TLOU2/Pruned1074','/Game/TLOU2/CaptureMatched1152').replace('assign_skeletal_materials_result.json','assign_capture_matched1152_materials_result.json')
exec(compile(code,path,'exec'),{'__name__':'correct_outfit_material_assignment'})
