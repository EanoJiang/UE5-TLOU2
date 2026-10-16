import os
ROOT='D:/TLOU2_UE5_8_Codex'
code=open(ROOT+'/Scripts/import_pruned_chunks_ue.py').read().replace("'/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'","'/Game/TLOU2/CaptureMatched1074/Skeleton/Ellie_CaptureMatched1074_SkeletonCarrier_Skeleton'").replace("'/Exports/PrunedArmature'","'/Exports/CaptureMatchedChunks'").replace("'/Game/TLOU2/Pruned1074/'","'/Game/TLOU2/CaptureMatched1074/'").replace("'/Exports/import_pruned_chunks_result.json'","'/Exports/import_capture_matched_chunks_result.json'")
exec(compile(code,ROOT+'/Scripts/import_pruned_chunks_ue.py','exec'))
