import os, json, hashlib
from datetime import datetime, timezone

ROOT = r"D:/TLOU2_UE5_8_Codex"
path = os.path.join(ROOT, "Content", "TLOU2", "Reports", "artifact_manifest_exact.json")
doc = json.load(open(path, encoding="utf-8"))
doc["generated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
doc["decoded_textures"] = 340

wanted = [
    "Blender/Ellie_Patrol_Catalog_Exact.blend",
    "Exports/Ellie_Patrol_Catalog_Exact.fbx",
    "Exports/Ellie_Patrol_Catalog_Exact.glb",
    "Exports/Ellie_Patrol_Catalog_ExactStatic.fbx",
    "Exports/Ellie_Patrol_Catalog_Exact_Preview.png",
    "Exports/Ellie_Patrol_AnimationPreview.gif",
    "Exports/Ellie_Patrol_AnimationPreview.mp4",
    "Exports/Ellie_Patrol_ExactAnimationPreview.gif",
    "Exports/Ellie_Patrol_ExactAnimationPreview_report.json",
    "Exports/Ellie_Patrol_ExactBody.fbx",
    "Exports/Ellie_Patrol_ExactBody.glb",
    "Exports/Ellie_Patrol_ExactBody_Preview.png",
    "Exports/Ellie_1074_SkeletonProbe.fbx",
    "Exports/Ellie_1074_RootMotion_Animation.fbx",
    "Exports/Ellie_1074_RootMotion_AnimationProbe.fbx",
    "Exports/Ellie_1074_RootMotion_AnimationProbe.csv",
    "Exports/AnimationSources/animation_source_manifest.json",
    "Exports/AnimationSources/DecodedRawChannels/codec_evidence/ellie-prone-lg-aim-strafe-0-fw_codec_frame_bytes.csv",
    "Exports/AnimationSources/ANIMATION_DECODE_REPORT.md",
    "Exports/reduced_groups_summary.json",
    "Exports/Ellie_Patrol_Catalog_ReducedGroups.fbx",
    "Exports/TexturesDecoded/texture_decode_manifest.json",
    "Content/TLOU2/Reports/texture_decode_validation.json",
    "Content/TLOU2/Reports/TEXTURE_DECODE_REPORT.md",
    "Scripts/extract_nd_pak_fake.py",
    "Scripts/decode_local_textures.py",
    "Scripts/verify_texture_decode.py",
    "Scripts/refresh_artifact_manifest.py",
    "Scripts/vendor/texture2ddecoder/__init__.py",
    "Scripts/vendor/texture2ddecoder/_texture2ddecoder.pyd",
    "Blender/build_full_patrol.py",
    "Scripts/import_exact_catalog_ue.py",
    "Scripts/import_exact_static_ue.py",
    "Scripts/import_exact_body_skeletal_ue.py",
    "Scripts/import_rootmotion_probe.py",
    "Scripts/import_reduced1074.py",
    "Scripts/create_skeletal_catalog_map.py",
    "Scripts/verify_final_ue.py",
    "Scripts/verify_exact_blend.py",
    "Scripts/make_pruned_armature_fbx.py",
    "Scripts/make_fullbone_pruned_chunks.py",
    "Scripts/import_pruned_chunks_ue.py",
    "Scripts/import_fullbone_chunks_ue.py",
    "Scripts/verify_pruned_chunks.py",
    "Scripts/assign_skeletal_materials.py",
    "Scripts/create_chunked_skeletal_map.py",
    "Scripts/create_raw_root_candidate_catalog_map.py",
    "Scripts/repair_serialized_animation_bindings_ue.py",
    "Scripts/enable_animation_root_motion_ue.py",
    "Scripts/verify_animation_interchange_ue.py",
    "Scripts/decode_nd_anim_stream.py",
    "Scripts/build_animation_source_reports.py",
    "Scripts/make_animation_fbx.py",
    "Scripts/render_exact_animation_preview.py",
    "Scripts/import_decoded_materials_ue.py",
    "Scripts/verify_ue_materials.py",
    "Content/TLOU2/Maps/ElliePatrolCatalog.umap",
    "Content/TLOU2/Maps/ElliePatrolCatalogSkeletal.umap",
    "Content/TLOU2/Maps/ElliePatrolChunkedSkeletal.umap",
    "Content/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial.umap",
    "Content/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate.umap",
    "Content/TLOU2/Reports/VALIDATION_REPORT.md",
    "Content/TLOU2/Reports/VALIDATION_RECHECK_2026-10-16.md",
    "Content/TLOU2/Reports/UE_IMPORT_REPORT.md",
    "Content/TLOU2/Reports/UE_TEXTURE_MATERIAL_REPORT.json",
    "Content/TLOU2/Reports/UE_TEXTURE_MATERIAL_VERIFY.json",
    "Content/TLOU2/Reports/ROOT_MOTION_REPORT.md",
    "Content/TLOU2/Reports/ANIMATION_SOURCE_MAP.md",
    "Content/TLOU2/Reports/ANIMATION_SOURCE_DECODE_EVIDENCE.json",
    "Content/TLOU2/Reports/ELLIE_ANIMATION_ASSET_CATALOG.csv",
    "Content/TLOU2/Reports/ROOT_MOTION_SOURCE_EVIDENCE.md",
    "Content/TLOU2/Reports/root_motion_source_timeline.csv",
    "Exports/final_ue_verification.json",
    "Exports/rootmotion_enable_result.json",
    "Exports/rootmotion_probe_verify.json",
    "Exports/rootmotion_fbx_verification.json",
    "Exports/exact_blend_validation.json",
    "Exports/pruned_armature_manifest.json",
    "Exports/fullbone_pruned_manifest.json",
    "Exports/pruned_fbx_validation.json",
    "Exports/fullbone_fbx_validation.json",
    "Exports/verify_pruned_ue.json",
    "Exports/import_pruned_chunks_result.json",
    "Exports/pruned_chunks_verify.json",
    "Exports/chunked_skeletal_map_result.json",
    "Exports/raw_root_candidate_catalog_map_result.json",
    "Exports/serialized_animation_bindings_repair.json",
    "Exports/animation_root_motion_settings.json",
    "Exports/animation_interchange_ue_verification.json",
    "Content/TLOU2/Reports/ANIMATION_INTERCHANGE_UE_VERIFICATION.md",
    "Exports/assign_skeletal_materials_result.json",
    "Blender/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw.blend",
    "Exports/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw.fbx",
    "Exports/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_AnimOnly.fbx",
    "Exports/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_AnimOnly2.fbx",
    "Exports/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe.fbx",
    "Content/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim.uasset",
    "Content/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe.uasset",
    "Exports/raw_root_candidate_metadata.json",
    "Exports/Ellie_RawRootCandidate_0FW_UE_RootTrajectory.csv",
    "Content/TLOU2/Reports/RAW_ROOT_CANDIDATE_REPORT.md",
    "Blender/Ellie_Patrol_RawRootCandidate_90LFW.blend",
    "Exports/Ellie_1074_RawRootCandidate_ellie-prone-lg-aim-strafe-90l-fw.fbx",
    "Exports/Ellie_1074_RawRootCandidate_ellie-prone-lg-aim-strafe-90l-fw.csv",
    "Exports/Ellie_Patrol_RawRootCandidate_90LFW.gif",
    "Exports/Ellie_Patrol_RawRootCandidate_90LFW_report.json",
    "Exports/Ellie_Patrol_RawRootCandidate_0FW.gif",
    "Exports/Ellie_Patrol_RawRootCandidate_0FW_report.json",
    "Content/TLOU2/Reports/ROOT_CHANNEL_TRAJECTORY_EVIDENCE.md",
    "Content/TLOU2/Reports/ROOT_TRAJECTORY_CORRECTION.md",
    "Content/TLOU2/Reports/movement_root_trajectory.csv",
    "Content/TLOU2/Reports/movement_root_trajectory_evidence.json",
    "Content/TLOU2/Reports/rawchannels_decode_manifest.json",
    "Content/TLOU2/Reports/ROOT_CHANNEL_DECODE_EVIDENCE.md",
    "Content/TLOU2/Reports/root_channel_tracks.csv",
    "Content/TLOU2/Reports/named_root_channel_catalog.csv",
    "Content/TLOU2/Reports/named_root_trajectory_samples.csv",
    "Content/TLOU2/Reports/named_root_trajectory_samples.json",
    "Content/TLOU2/Reports/NAMED_ROOT_CHANNEL_CATALOG.md",
    "Content/TLOU2/Reports/raw_decoder_verification.json",
    "Content/TLOU2/Reports/DELIVERY_INDEX.md",
    "Content/TLOU2/Reports/DELIVERY_INDEX.json",
    "Scripts/build_deliverable_index.py",
    "Scripts/decode_root_candidate_tracks.py",
    "Scripts/decode_nd_rawchannels.py",
    "Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.json",
    "Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.csv",
    "Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.md",
    "Content/TLOU2/Reports/ORBISANIM_CODEC_EXECUTABLE_EVIDENCE.json",
    "Content/TLOU2/Reports/ORBISANIM_CODEC_EXECUTABLE_EVIDENCE.md",
    "Content/TLOU2/Reports/ORBISANIM_QUAT_SCALE_EVIDENCE.json",
    "Content/TLOU2/Reports/ORBISANIM_QUAT_SCALE_EVIDENCE.md",
    "Content/TLOU2/Reports/ANIMATION_DECODE_STATUS.md",
    "Content/TLOU2/Reports/CODEC_41430102_STRUCTURE_TARGET.md",
    "Content/TLOU2/Reports/CODEC_41430102_STRUCTURE_TARGET.json",
    "Content/TLOU2/Reports/CODEC_41430102_HEADER_CORRECTION.md",
    "Content/TLOU2/Reports/CODEC_41430102_HEADER_CORRECTION.json",
    "Scripts/probe_codec_41430102_header.py",
    "Scripts/probe_codec_destination_tables.py",
    "Content/TLOU2/Reports/CODEC_41430102_DESTINATION_TABLES.md",
    "Content/TLOU2/Reports/CODEC_41430102_DESTINATION_TABLES.json",
    "Scripts/probe_codec_41430102_structure.js",
]
items = []
for rel in wanted:
    full = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.isfile(full):
        continue
    h = hashlib.sha256()
    with open(full, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    items.append({"path": rel, "bytes": os.path.getsize(full), "sha256": h.hexdigest()})
# Keep the small, redistributable source package mirror auditable without
# hard-coding a list that can drift as another outfit part is added.
source_root = os.path.join(ROOT, "Content", "TLOU2", "SourcePaks")
for full in sorted((p for p in __import__('pathlib').Path(source_root).rglob('*') if p.is_file())):
    rel = full.relative_to(ROOT).as_posix()
    if any(x["path"] == rel for x in items):
        continue
    h = hashlib.sha256()
    with open(full, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    items.append({"path": rel, "bytes": full.stat().st_size, "sha256": h.hexdigest()})
for folder in (os.path.join(ROOT, "Exports", "PrunedArmature"), os.path.join(ROOT, "Exports", "FullBonePruned"), os.path.join(ROOT, "Content", "TLOU2", "Pruned1074"), os.path.join(ROOT, "Content", "TLOU2", "FullBone1074")):
    if not os.path.isdir(folder):
        continue
    for full in sorted(__import__('pathlib').Path(folder).rglob('*')):
        if not full.is_file():
            continue
        rel = full.relative_to(ROOT).as_posix()
        if any(x["path"] == rel for x in items):
            continue
        h = hashlib.sha256()
        with open(full, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        items.append({"path": rel, "bytes": full.stat().st_size, "sha256": h.hexdigest()})
doc["artifacts"] = items
json.dump(doc, open(path, "w", encoding="utf-8"), indent=2)
print("ARTIFACT_MANIFEST", len(items), "items", "decoded_textures", doc["decoded_textures"])
