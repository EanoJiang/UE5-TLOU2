ROOT='D:/TLOU2_UE5_8_Codex'
path=ROOT+'/Scripts/import_original_0fw_animation_ue.py'
code=open(path).read().replace('CaptureMatched1074','CaptureMatched1152').replace('Ellie_Original_0FW_AnimationCarrier','Ellie_Patrol_CapturedSkinPose_UEHoldCarrier').replace('import_original_0fw_animation_result.json','import_captured_skin_pose_animation_result.json')
exec(compile(code,path,'exec'),{'__name__':'captured_animation_import'})
