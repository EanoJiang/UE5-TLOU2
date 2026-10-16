ROOT='D:/TLOU2_UE5_8_Codex'
for name in ['import_capture_matched1152_skeleton_ue.py','apply_reconstructed_eye_material_ue.py','import_capture_matched1152_chunks_ue.py','configure_capture_mesh_precision_ue.py']:
    path=ROOT+'/Scripts/'+name
    exec(compile(open(path).read(),path,'exec'),{'__name__':'capture_neutral_pipeline'})
