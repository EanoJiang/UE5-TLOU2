import unreal, json, os

ROOT = r"D:/TLOU2_UE5_8_Codex"
out = {"engine": "UE 5.8", "checks": {}, "errors": []}

def check(name, value, detail=None):
    ok = bool(value)
    out["checks"][name] = {"ok": ok, "detail": detail}
    if not ok:
        out["errors"].append(name)
    return ok

static_paths = unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/ExactStatic', recursive=True)
static_meshes = [unreal.load_asset(p) for p in static_paths]
static_meshes = [a for a in static_meshes if isinstance(a, unreal.StaticMesh)]
slot_count = 0
bound_count = 0
for sm in static_meshes:
    for s in sm.get_editor_property('static_materials'):
        slot_count += 1
        mi = s.get_editor_property('material_interface')
        if mi and str(mi.get_name()).startswith('M_ND_'):
            bound_count += 1
check('static_mesh_count', len(static_meshes) == 35, len(static_meshes))
check('static_material_slots', slot_count == 35, slot_count)
check('static_material_bindings', bound_count == 32, bound_count)

probe_sk = unreal.load_asset('/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton')
body = unreal.load_asset('/Game/TLOU2/ExactBody1074/Ellie_Patrol_ExactBody')
anim = unreal.load_asset('/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim')
probe_pose = probe_sk.get_reference_pose() if probe_sk else None
body_sk = body.get_editor_property('skeleton') if body else None
anim_sk = anim.get_editor_property('skeleton') if anim else None
probe_bones = len(probe_pose.get_bone_names()) if probe_pose else 0
body_bones = len(body_sk.get_reference_pose().get_bone_names()) if body_sk else 0
anim_bones = len(anim_sk.get_reference_pose().get_bone_names()) if anim_sk else 0
check('probe_skeleton', probe_sk is not None and probe_bones == 1075, probe_bones)
check('body_skeletal_mesh', body is not None and body_sk == probe_sk and body_bones == 1075, {'bones': body_bones, 'same_skeleton': body_sk == probe_sk})
seq_len = float(anim.get_editor_property('sequence_length')) if anim else 0.0
root_enabled = bool(anim.get_editor_property('enable_root_motion')) if anim else False
check('animation_sequence', anim is not None and anim_sk == probe_sk and abs(seq_len - 2.6333334) < 0.01 and root_enabled, {'bones': anim_bones, 'seconds': seq_len, 'root_motion': root_enabled, 'same_skeleton': anim_sk == probe_sk})

check('catalog_map', unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolCatalog'), True)
check('skeletal_catalog_map', unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolCatalogSkeletal'), True)
check('chunked_skeletal_map', unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolChunkedSkeletal'), True)
check('chunked_skeletal_material_map', unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial'), True)
check('catalog_ui_map', unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolCatalogUI_Final') and unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolCatalogUI'), True)

chunk_assets = []
chunk_bound = 0
chunk_slots = 0
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Pruned1074', recursive=True):
    a = unreal.load_asset(p)
    if not isinstance(a, unreal.SkeletalMesh):
        continue
    chunk_assets.append(a)
    chunk_sk = a.get_editor_property('skeleton')
    if chunk_sk == probe_sk:
        pass
    for slot in a.get_editor_property('materials'):
        chunk_slots += 1
        mi = slot.get_editor_property('material_interface')
        if mi and str(mi.get_name()).startswith('M_ND_'):
            chunk_bound += 1
check('chunked_skeletal_assets', len(chunk_assets) == 5 and all(a.get_editor_property('skeleton') == probe_sk for a in chunk_assets), {'count': len(chunk_assets), 'bones': [len(a.get_editor_property('skeleton').get_reference_pose().get_bone_names()) for a in chunk_assets]})
map_report = os.path.join(ROOT, 'Exports', 'chunked_skeletal_map_result.json')
assign_report = os.path.join(ROOT, 'Exports', 'assign_skeletal_materials_result.json')
map_bound = 0
assign_bound = 0
if os.path.isfile(map_report):
    map_bound = int(json.load(open(map_report, encoding='utf-8')).get('material_bindings', 0))
if os.path.isfile(assign_report):
    assign_bound = int(json.load(open(assign_report, encoding='utf-8')).get('bound', 0))
check('chunked_material_bindings', map_bound == 26 and assign_bound == 26, {'slots': chunk_slots, 'asset_bound': chunk_bound, 'map_component_bound': map_bound, 'assign_bound': assign_bound})

# Capture-facing catalog additions: the existing animated outfit map now also
# contains the presentation plinth and the cropped instruction strip material.
check('catalog_ui_reference_assets',
      unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Proxy/Catalog_Plinth') and
      unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Materials/MI_CatalogInstructionBar') and
      unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Reference/T_CatalogInstructionBar'),
      {'plinth': unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Proxy/Catalog_Plinth'),
       'instruction_material': unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Materials/MI_CatalogInstructionBar'),
       'instruction_texture': unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Reference/T_CatalogInstructionBar')})

# Source-unit review surface and UE animation round-trip verification.  This is
# intentionally separate from the exact probe: the named ND clip's full codec
# semantics remain unresolved, while its raw root X samples are directly
# checkable after import.
raw_anim = unreal.load_asset('/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim')
raw_anim_skel = raw_anim.get_editor_property('skeleton') if raw_anim else None
raw_len = float(raw_anim.get_editor_property('sequence_length')) if raw_anim else 0.0
raw_root_enabled = bool(raw_anim.get_editor_property('enable_root_motion')) if raw_anim else False
check('raw_root_candidate_animation', raw_anim is not None and raw_anim_skel == probe_sk and abs(raw_len - 2.6333334) < 0.01 and raw_root_enabled,
      {'asset': raw_anim.get_path_name() if raw_anim else None, 'bones': len(raw_anim_skel.get_reference_pose().get_bone_names()) if raw_anim_skel else 0, 'seconds': raw_len, 'root_motion': raw_root_enabled})
check('raw_root_candidate_map', unreal.EditorAssetLibrary.does_asset_exist('/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate'), True)
anim_interchange_report = os.path.join(ROOT, 'Exports', 'animation_interchange_ue_verification.json')
if os.path.isfile(anim_interchange_report):
    try:
        doc = json.load(open(anim_interchange_report, encoding='utf-8'))
        check('animation_interchange_ue_report', bool(doc.get('pass')), {'errors': doc.get('errors', []), 'roundtrip': doc.get('raw_root_channel_roundtrip', {})})
    except Exception as e:
        check('animation_interchange_ue_report', False, repr(e))
else:
    check('animation_interchange_ue_report', False, 'missing')
binding_report = os.path.join(ROOT, 'Exports', 'serialized_animation_bindings_repair.json')
if os.path.isfile(binding_report):
    try:
        doc = json.load(open(binding_report, encoding='utf-8'))
        check('serialized_animation_bindings', bool(doc.get('pass')), {'maps': list(doc.get('maps', {}).keys())})
    except Exception as e:
        check('serialized_animation_bindings', False, repr(e))
else:
    check('serialized_animation_bindings', False, 'missing')

manifest = os.path.join(ROOT, 'Exports', 'AnimationSources', 'animation_source_manifest.json')
if os.path.isfile(manifest):
    doc = json.load(open(manifest, encoding='utf-8'))
    codecs = [c for s in doc.get('sources', []) for ch in s.get('chunks', []) for c in ch.get('codec', [])]
    raw = [r for s in doc.get('sources', []) for ch in s.get('chunks', []) for r in ch.get('resources', []) if r.get('type') == 'ANIM_RAWCHANNELS']
    check('animation_source_manifest', len(doc.get('sources', [])) == 7 and len(codecs) == 1164 and len(raw) == 1227, {'sources': len(doc.get('sources', [])), 'codec_payloads': len(codecs), 'rawchannels': len(raw)})
else:
    check('animation_source_manifest', False, 'missing')

tex_manifest = os.path.join(ROOT, 'Exports', 'TexturesDecoded', 'texture_decode_manifest.json')
if os.path.isfile(tex_manifest):
    rows = json.load(open(tex_manifest, encoding='utf-8'))
    check('decoded_texture_manifest', len(rows) == 340 and all(r.get('decoded') and os.path.isfile(r.get('decoded_path', '')) for r in rows), len(rows))
else:
    check('decoded_texture_manifest', False, 'missing')

out['pass'] = not out['errors']
json.dump(out, open(os.path.join(ROOT, 'Exports', 'final_ue_verification.json'), 'w', encoding='utf-8'), indent=2)
unreal.log('FINAL_UE_VERIFY ' + json.dumps(out, ensure_ascii=False))
if out['errors']:
    raise RuntimeError('final UE verification failed: ' + ','.join(out['errors']))
