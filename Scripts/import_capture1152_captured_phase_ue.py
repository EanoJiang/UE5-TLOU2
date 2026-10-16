ROOT='D:/TLOU2_UE5_8_Codex'
for name in ['import_captured_skin_pose_animation_ue.py','import_captured_skin_pose_chunks_ue.py','configure_capture_mesh_precision_ue.py','create_capture_matched_catalog_map_ue.py','verify_capture_matched_catalog_map_ue.py']:
    path=ROOT+'/Scripts/'+name
    exec(compile(open(path).read(),path,'exec'),{'__name__':'capture_captured_pipeline'})
