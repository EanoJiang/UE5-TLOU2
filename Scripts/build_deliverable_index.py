from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

ROOT = Path(r'D:/TLOU2_UE5_8_Codex')
REPORT_DIR = ROOT / 'Content/TLOU2/Reports'
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def row(path, role, status, evidence='', note=''):
    p = ROOT / path
    return {'path': path.replace('\\','/'), 'exists': p.exists(), 'bytes': p.stat().st_size if p.exists() else 0,
            'role': role, 'status': status, 'evidence': evidence, 'note': note}

items = [
 row('TLOU2Codex.uproject', 'UE 5.8 project entry point', 'verified', 'open with D:/EpicGame/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'),
 row('Content/TLOU2/Maps/ElliePatrolCatalog.umap', '35-part exact static catalog map', 'verified', 'Exports/final_ue_verification.json: catalog_map'),
 row('Content/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial.umap', 'full animated outfit showcase map with 5 shared-skeleton chunks and 26 material bindings', 'verified', 'Exports/final_ue_verification.json: chunked_skeletal_material_map'),
 row('Content/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate.umap', 'source-unit review map with 5 outfit chunks driven by the named 0FW raw root candidate', 'evidence only', 'Exports/animation_interchange_ue_verification.json', 'ND codec units and full bone semantics remain unresolved'),
 row('Content/TLOU2/Reference/catalog_instruction_bar.png', 'cropped capture instruction strip used by the catalog UI material', 'verified', 'Content/TLOU2/Reports/UE_VERIFICATION_COMMANDLET_2026-10-16.md'),
 row('Content/TLOU2/Materials/MI_CatalogInstructionBar.uasset', 'capture-facing instruction strip material instance', 'verified', 'Exports/final_ue_verification.json: catalog_ui_reference_assets'),
 row('Content/TLOU2/Maps/ElliePatrolCatalogSkeletal.umap', 'single exact body skeletal showcase', 'verified', 'Exports/final_ue_verification.json: skeletal_catalog_map'),
 row('Exports/Ellie_Patrol_Catalog_Exact.fbx', 'combined exact outfit interchange source', 'verified', 'Exports/exact_blend_validation.json'),
 row('Exports/Ellie_Patrol_Catalog_Exact.glb', 'combined exact outfit glTF interchange source', 'verified', 'Exports/exact_blend_validation.json'),
 row('Exports/Ellie_Patrol_Catalog_Exact.gltf', 'editable JSON glTF source split from the exact outfit GLB', 'verified', 'Scripts/export_gltf_sources.py'),
 row('Exports/Ellie_Patrol_Catalog_Exact.bin', 'binary buffer for the exact outfit JSON glTF source', 'verified', 'Scripts/export_gltf_sources.py'),
 row('Blender/Ellie_Patrol_Catalog_Exact.blend', 'editable Blender source: exact geometry, 1,074 game bones, skin weights and materials', 'verified', 'Exports/exact_blend_validation.json'),
 row('Exports/Ellie_1074_SkeletonManifest.json', 'machine-readable 1,074-joint hierarchy with rest transforms and FNV-1a64 hashes', 'verified', 'Content/TLOU2/Reports/SKELETON_MANIFEST.md'),
 row('Exports/Ellie_Patrol_ExactBody.fbx', 'exact body/clothing skeletal FBX', 'verified', 'Exports/fullbone_fbx_validation.json'),
 row('Exports/Ellie_Patrol_ExactBody.glb', 'exact body/clothing glTF', 'verified', 'Exports/exact_blend_validation.json'),
 row('Exports/Ellie_Patrol_ExactBody.gltf', 'editable JSON glTF body/clothing source split from the GLB', 'verified', 'Scripts/export_gltf_sources.py'),
 row('Exports/Ellie_Patrol_ExactBody.bin', 'binary buffer for the body/clothing JSON glTF source', 'verified', 'Scripts/export_gltf_sources.py'),
 row('Exports/Ellie_1074_SkeletonProbe.fbx', '1,074-bone probe skeleton source', 'verified', 'Exports/final_ue_verification.json: probe_skeleton=1075 UE names including Blender root'),
 row('Exports/Ellie_1074_RootMotion_AnimationProbe.fbx', '80-frame, 30-fps root-motion interchange probe', 'verified probe', 'Exports/rootmotion_fbx_verification.json; source-unit probe only'),
 row('Exports/Ellie_1074_RootMotion_AnimationProbe.csv', 'frame-by-frame probe root trajectory', 'verified probe', 'Exports/rootmotion_fbx_verification.json'),
 row('Exports/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw.fbx', 'raw source-unit candidate built from a real named movement clip', 'evidence only', 'Content/TLOU2/Reports/RAW_ROOT_CANDIDATE_REPORT.md', 'ND channel interpolation, units and bone mapping remain unresolved'),
 row('Content/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim.uasset', 'UE 5.8 AnimSequence import of the 80-frame raw root candidate', 'evidence only', 'Exports/animation_interchange_ue_verification.json', '80/80 poses; root-X max error 0'),
 row('Exports/Ellie_RawRootCandidate_0FW_UE_RootTrajectory.csv', 'UE-evaluated root trajectory paired with source raw samples', 'evidence only', 'Exports/animation_interchange_ue_verification.json', '80 rows; max root-X error 0; units unresolved'),
 row('Blender/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw.blend', 'editable raw root candidate Blender scene', 'evidence only', 'Content/TLOU2/Reports/RAW_ROOT_CANDIDATE_REPORT.md'),
 row('Exports/Ellie_Patrol_RawRootCandidate_0FW.gif', 'rendered preview of the real 0FW raw root-channel candidate', 'evidence only', 'Exports/Ellie_Patrol_RawRootCandidate_0FW_report.json'),
 row('Exports/Ellie_Patrol_RawRootCandidate_0FW_report.json', 'raw root candidate preview report', 'evidence only', 'Content/TLOU2/Reports/RAW_ROOT_CANDIDATE_REPORT.md'),
 row('Exports/Ellie_Patrol_RawRootCandidate_0FW.gif', '80-frame preview of the named 0-fw source-unit root candidate', 'evidence only', 'Exports/Ellie_Patrol_RawRootCandidate_0FW_report.json'),
 row('Exports/AnimationSources/animation_source_manifest.json', 'indexed original Ellie animation source packages', 'verified bytes', 'Content/TLOU2/Reports/ANIMATION_SOURCE_DECODE_EVIDENCE.json', '1,164 codec payloads and 1,227 raw channel resources'),
 row('Exports/AnimationSources/DecodedRawChannels/codec_evidence/ellie-prone-lg-aim-strafe-0-fw_codec_frame_bytes.csv', 'exact 80-frame codec byte stream export', 'verified bytes', 'Content/TLOU2/Reports/CODEC_41430102_STRUCTURE_TARGET.md'),
 row('Content/TLOU2/Reports/movement_root_trajectory.csv', 'decoded raw root-channel storage rows', 'evidence only', 'Content/TLOU2/Reports/ROOT_CHANNEL_TRAJECTORY_EVIDENCE.md', 'not claimed as semantic root motion'),
 row('Exports/TexturesDecoded/texture_decode_manifest.json', 'decoded texture manifest', 'verified', 'Content/TLOU2/Reports/texture_decode_validation.json', '340/340 decoded local VRAM descriptors'),
 row('Content/TLOU2/Reports/UE_TEXTURE_MATERIAL_REPORT.json', 'UE exact material creation and slot assignment report', 'verified', '32/35 slots and 26 exact materials'),
 row('Exports/Ellie_Patrol_Catalog_Exact_Preview.png', 'exact outfit still preview', 'verified', 'Content/TLOU2/Reports/VALIDATION_REPORT.md'),
 row('Exports/Ellie_Patrol_ExactAnimationPreview.gif', 'exact outfit animated preview', 'verified probe', 'Exports/Ellie_Patrol_ExactAnimationPreview_report.json'),
 row('Exports/deliverable_verification_2026-10-16.json', 'pure-Python portable deliverable verification', 'verified', 'Content/TLOU2/Reports/DELIVERABLE_VERIFICATION_2026-10-16.md'),
 row('Content/TLOU2/Reports/final_ue_verification.json', 'UE 5.8 final verification', 'verified', 'Exports/final_ue_verification.json', 'the canonical JSON is under Exports; this row points to it'),
 row('Content/TLOU2/Reports/VALIDATION_REPORT.md', 'full provenance and validation report', 'verified', 'includes capture path, package provenance, geometry, textures, UE maps and caveats'),
 row('Content/TLOU2/Reports/CODEC_41430102_STRUCTURE_TARGET.md', 'target 0x41430102 codec structure evidence', 'evidence only', 'descriptor and section metadata for ellie-prone-lg-aim-strafe-0-fw; proprietary decode unresolved'),
 row('Content/TLOU2/Reports/CODEC_41430102_DESTINATION_TABLES.md', '48-byte transform destination offset pattern and sentinels', 'verified evidence', 'Scripts/probe_codec_destination_tables.py', 'bone identity and dynamic compressed layout unresolved'),
 row('Content/TLOU2/Reports/CODEC_41430102_HEADER_CORRECTION.md', 'bindpose cross-check correcting +0x30 to section/table offset 0x120', 'verified evidence', 'Scripts/probe_codec_41430102_header.py', 'descriptor count remains unresolved'),
 row('Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.json', 'historical rejected source-bit-offset q48 probe', 'evidence only', 'Content/TLOU2/Reports/ANIMATION_DECODE_STATUS.md', 'source-bit-offset assumption withdrawn; see CODEC_41430102_DESTINATION_TABLES.md'),
 row('Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.csv', 'CSV audit of rejected source-bit-offset quaternion words', 'evidence only', 'Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.md'),
 row('Content/TLOU2/Reports/ORBISANIM_CODEC_EXECUTABLE_EVIDENCE.md', 'installed executable routine-name evidence', 'evidence only', 'routine strings only; not proof of a completed decode'),
 row('Content/TLOU2/Reports/ORBISANIM_QUAT_SCALE_EVIDENCE.md', 'executable quantizer scale evidence', 'evidence only', 'sqrt(1/2)/16384 constants; exact codec call path unresolved'),
 row('Content/TLOU2/Reports/ANIMATION_DECODE_STATUS.md', 'animation decode boundary and partial-artifact handoff', 'verified', 'lists exact bytes, candidate quaternions, raw root candidate and limitations'),
 row('Content/TLOU2/Reports/ANIMATION_INTERCHANGE_UE_VERIFICATION.md', 'UE 5.8 animation asset, root-motion and serialized map-binding verification', 'verified evidence', 'Exports/animation_interchange_ue_verification.json (pass=true)'),
 row('Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.md', 'historical rejected source-bit-offset quaternion table', 'evidence only', 'source-bit-offset assumption withdrawn; destination transform offsets verified'),
 row('Content/TLOU2/Reports/ORBISANIM_CODEC_EXECUTABLE_EVIDENCE.md', 'executable-side OrbisAnim codec routine evidence', 'evidence only', 'routine names and constants only; no semantic mapping claim'),
 row('Content/TLOU2/Reports/ANIMATION_DECODE_STATUS.md', 'primary target animation decode boundary and handoff status', 'evidence only', 'explicitly separates byte-preserved source, destination layout, raw root data and unresolved 1,074-bone reconstruction'),
 row('Content/TLOU2/Reports/BONE_CHANNEL_HASH_MAPPING.md', 'bone/channel hash mapping audit', 'evidence only', '1074/1074 FNV-1a bone hashes verified; animation channel hashes require codec semantics'),
]
# ensure the verification row points to the canonical final verifier location
for item in items:
    if item['role'] == 'UE 5.8 final verification':
        item['path'] = 'Exports/final_ue_verification.json'
        item['exists'] = (ROOT/item['path']).exists()
        item['bytes'] = (ROOT/item['path']).stat().st_size if item['exists'] else 0

summary = {
    'generated_utc': datetime.now(timezone.utc).isoformat(),
    'project_root': str(ROOT),
    'capture': r'D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture',
    'counts': {'items': len(items), 'existing': sum(1 for x in items if x['exists'])},
    'verified_metrics': {'game_bones': 1074, 'ue_probe_bones_including_blender_root': 1075, 'lod0_meshes': 35, 'vertices': 117109, 'decoded_textures': 340, 'exact_materials': 26, 'bound_material_slots': 32, 'root_probe_frames': 80, 'root_probe_fps': 30},
    'items': items,
    'semantic_boundary': 'Original Naughty Dog ANIM_RAWCHANNELS bytes are preserved and structurally decoded. The proprietary interpolation/quantization and channel-to-bone/world-axis mapping are unresolved. The UE AnimSequence and GIF are explicitly an interchange probe; the raw candidate is evidence only.',
}
(REPORT_DIR/'DELIVERABLE_INDEX.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# Ellie Patrol outfit deliverable index', '', f"Generated: `{summary['generated_utc']}`", '', f"Capture: `{summary['capture']}`", '', 'This index is a path-oriented handoff for the UE 5.8 project and interchange sources. Status labels preserve the boundary between verified interchange output and storage-level evidence from the original Naughty Dog animation packages.', '', '## Verified metrics', '', '| Metric | Value |', '|---|---:|']
for k,v in summary['verified_metrics'].items(): lines.append(f'| {k} | {v} |')
lines += ['', '## Deliverables', '', '| Path | Role | Status | Evidence / note |', '|---|---|---|---|']
for x in items:
    p = f"`{x['path']}`" if x['exists'] else f"`{x['path']}` (missing)"
    ev = x['evidence'] + (f" — {x['note']}" if x['note'] else '')
    lines.append(f"| {p} | {x['role']} | {x['status']} | {ev} |")
lines += ['', '## Animation boundary', '', summary['semantic_boundary'], '', '## Canonical reports', '', '- `Content/TLOU2/Reports/VALIDATION_REPORT.md` — full provenance and validation narrative.', '- `Content/TLOU2/Reports/VALIDATION_RECHECK_2026-10-16.md` — fresh Blender/UE/texture verification.', '- `Exports/final_ue_verification.json` — UE 5.8 commandlet checks (`pass=true`).', '- `Exports/deliverable_verification_2026-10-16.json` — portable file-level verification with SHA-256 hashes.', '- `Content/TLOU2/Reports/DELIVERABLE_VERIFICATION_2026-10-16.md` — human-readable portable verification table.', '- `Content/TLOU2/Reports/CODEC_41430102_QUAT48_CANDIDATES.md` — 48-bit storage candidate table with explicit uncertainty.', '- `Content/TLOU2/Reports/ORBISANIM_CODEC_EXECUTABLE_EVIDENCE.md` — executable-side routine/constant evidence.', '- `Content/TLOU2/Reports/ROOT_CHANNEL_TRAJECTORY_EVIDENCE.md` — corrected raw channel layout and sample counts.', '- `Content/TLOU2/Reports/NAMED_ROOT_CHANNEL_CATALOG.md` — named ANIM to raw channel linkage.', '']
(REPORT_DIR/'DELIVERABLE_INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({'json': str(REPORT_DIR/'DELIVERABLE_INDEX.json'), 'md': str(REPORT_DIR/'DELIVERABLE_INDEX.md'), 'items': len(items), 'existing': sum(1 for x in items if x['exists'])}, ensure_ascii=False))
