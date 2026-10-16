ROOT='D:/TLOU2_UE5_8_Codex'
path=ROOT+'/Scripts/import_pruned_chunks_ue.py'
code=open(path).read().replace("'/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'","'/Game/TLOU2/CaptureMatched1152/Skeleton/Ellie_CaptureMatched1152_SkeletonCarrier_Skeleton'").replace("'/Exports/PrunedArmature'","'/Exports/CapturedSkinPoseChunks'").replace("'/Game/TLOU2/Pruned1074/'","'/Game/TLOU2/CaptureMatched1152/CapturedMeshes/'").replace("'/Exports/import_pruned_chunks_result.json'","'/Exports/import_captured_skin_pose_chunks_result.json'").replace('task.options = ui',"ui.get_editor_property('skeletal_mesh_import_data').set_editor_property('import_morph_targets', True)\n    task.options = ui")
code=code.replace("set_editor_property('import_morph_targets', True)","set_editor_property('import_morph_targets', True)\n    ui.get_editor_property('skeletal_mesh_import_data').set_editor_property('morph_threshold_position', .000001)")
exec(compile(code,path,'exec'),{'__name__':'captured_pose_mesh_import'})
path=ROOT+'/Scripts/assign_skeletal_materials.py'
code=open(path).read().replace('/Game/TLOU2/Pruned1074','/Game/TLOU2/CaptureMatched1152/CapturedMeshes').replace('assign_skeletal_materials_result.json','assign_captured_skin_pose_materials_result.json')
exec(compile(code,path,'exec'),{'__name__':'captured_pose_mesh_materials'})
