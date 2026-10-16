ROOT='D:/TLOU2_UE5_8_Codex'
code=open(ROOT+'/Scripts/import_original_0fw_animation_ue.py').read().replace('Ellie_Original_0FW_AnimationCarrier','Ellie16_Patrol_OriginalViewerPose_UEHoldCarrier').replace('import_original_0fw_animation_result.json','import_original_viewer_pose_result.json')
exec(compile(code,ROOT+'/Scripts/import_original_0fw_animation_ue.py','exec'))
