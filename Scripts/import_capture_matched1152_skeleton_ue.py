ROOT='D:/TLOU2_UE5_8_Codex'
path=ROOT+'/Scripts/import_capture_matched1390_skeleton_ue.py'
code=open(path).read().replace('1390','1152').replace('1391','1153')
exec(compile(code,path,'exec'),{'__name__':'correct_outfit_skeleton_import'})
