ROOT='D:/TLOU2_UE5_8_Codex'
code=open(ROOT+'/Scripts/export_original_0fw_ue_poses.py').read().replace('Ellie_Original_0FW_AnimationCarrier_Anim','Ellie16_Patrol_OriginalViewerPose_UEHoldCarrier_Anim').replace('ellie-prone-lg-aim-strafe-0-fw.json','model-viewer-ellie-16-patrol.json').replace('range(80)','range(2)').replace('original_0fw_ue_poses.json','original_viewer_ue_poses.json')
exec(compile(code,ROOT+'/Scripts/export_original_0fw_ue_poses.py','exec'))
