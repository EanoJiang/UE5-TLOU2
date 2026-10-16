"""Limited neutral/captured body reimport; no animation, skeleton or other mesh writes.

Run in the coordinated UE editor session after body FBX preparation. Geometry
and custom normals refresh only two existing SkeletalMesh asset paths. Preserve
shared skeleton, original material bindings, captured morph names, full influence
capacity and precision settings. Report actual saved-asset triangle tags without
assuming that the importer preserves repeated source primitives.
"""
import hashlib
import json
import re
import struct
from pathlib import Path

import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
SKELETON = '/Game/TLOU2/CaptureMatched1152/Skeleton/Ellie_CaptureMatched1152_SkeletonCarrier_Skeleton'
CASES = [('CaptureMatchedChunks', '/Game/TLOU2/CaptureMatched1152/body_clothing', False),
         ('CapturedSkinPoseChunks', '/Game/TLOU2/CaptureMatched1152/CapturedMeshes/body_clothing', True)]
NAME = 'Ellie_Patrol_body_clothing_Pruned'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def transform(value):
    return {'translation': list(value.translation.to_tuple()),
            'rotation': [value.rotation.x, value.rotation.y, value.rotation.z, value.rotation.w],
            'scale': list(value.scale3d.to_tuple())}


def skeleton_signature(skeleton):
    pose = skeleton.get_reference_pose()
    names = list(pose.get_bone_names())
    values = {str(n): transform(pose.get_bone_pose(n)) for n in names}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest(), len(names)


def animation_snapshot():
    rows = {}
    for path in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/CaptureMatched1152/Animations', recursive=True):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.AnimSequence):
            rows[asset.get_path_name()] = {'skeleton': asset.get_skeleton().get_path_name(),
                                          'seconds': float(asset.get_play_length())}
    return rows


def materials(mesh):
    return [(str(slot.get_editor_property('material_slot_name')),
             slot.get_editor_property('material_interface')) for slot in mesh.get_editor_property('materials')]


def morph_names(mesh):
    return sorted(m.get_name() for m in mesh.get_editor_property('morph_targets'))


def saved_asset_integer_tag(path, tag):
    asset_file = ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset')
    data = asset_file.read_bytes()
    needle = struct.pack('<i', len(tag)+1) + tag.encode() + b'\0'
    values = []
    for match in re.finditer(re.escape(needle), data):
        offset = match.end()
        length = struct.unpack_from('<i', data, offset)[0]
        if 1 < length < 20:
            value = data[offset+4:offset+4+length]
            if value.endswith(b'\0') and value[:-1].isdigit():
                values.append(int(value[:-1]))
    assert len(values) == 1, (path, tag, values)
    return values[0]


def main():
    exports = json.loads((ROOT/'Exports/restored_body_chunk_export_validation.json').read_text())
    assert exports['pass'] and len(exports['outputs']) == 2
    expected_hashes = {Path(row['fbx']).parent.name: row['fbx_sha256'] for row in exports['outputs']}
    skeleton = unreal.load_asset(SKELETON)
    assert isinstance(skeleton, unreal.Skeleton)
    before_skeleton, bones = skeleton_signature(skeleton)
    assert bones == 1153
    before_animations = animation_snapshot()
    subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    rows = []
    for folder, destination, captured in CASES:
        asset_path = destination+'/'+NAME
        mesh = unreal.load_asset(asset_path)
        assert isinstance(mesh, unreal.SkeletalMesh) and mesh.get_editor_property('skeleton') == skeleton
        old_materials = materials(mesh)
        old_by_name = {}
        for name, material in old_materials:
            assert name not in old_by_name or old_by_name[name] == material
            old_by_name[name] = material
        old_morphs = morph_names(mesh)
        old_triangles = saved_asset_integer_tag(asset_path, 'Triangles')
        source = ROOT/'Exports'/folder/(NAME+'.fbx')
        assert sha(source) == expected_hashes[folder]
        task = unreal.AssetImportTask()
        task.filename = str(source)
        task.destination_path = destination
        task.destination_name = NAME
        task.automated = True
        task.replace_existing = True
        task.replace_existing_settings = True
        task.save = True
        options = unreal.FbxImportUI()
        for name, value in {'import_mesh': True, 'import_as_skeletal': True, 'import_animations': False,
                            'import_materials': False, 'import_textures': False, 'create_physics_asset': False,
                            'skeleton': skeleton}.items():
            options.set_editor_property(name, value)
        data = options.get_editor_property('skeletal_mesh_import_data')
        for name, value in {'import_morph_targets': captured, 'morph_threshold_position': 0.000001,
                            'update_skeleton_reference_pose': False, 'use_t0_as_ref_pose': False,
                            'normal_import_method': unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
                            'compute_weighted_normals': False}.items():
            data.set_editor_property(name, value)
        task.options = options
        asset_tools.import_asset_tasks([task])
        imported = [unreal.load_asset(p) for p in task.imported_object_paths]
        imported_meshes = [a for a in imported if isinstance(a, unreal.SkeletalMesh)]
        assert len(imported_meshes) == 1 and imported_meshes[0].get_path_name().split('.')[0] == asset_path
        mesh = imported_meshes[0]
        assert mesh.get_editor_property('skeleton') == skeleton
        new_slots = mesh.get_editor_property('materials')
        assert set(str(s.get_editor_property('material_slot_name')) for s in new_slots) == set(old_by_name)
        for slot in new_slots:
            slot.set_editor_property('material_interface', old_by_name[str(slot.get_editor_property('material_slot_name'))])
        mesh.set_editor_property('materials', new_slots)
        settings = subsystem.get_lod_build_settings(mesh, 0)
        final_settings = {'bone_influence_limit': 12, 'use_high_precision_skin_weights': True,
                          'use_full_precision_u_vs': True, 'use_high_precision_tangent_basis': True,
                          'morph_threshold_position': 0.000001, 'recompute_normals': False,
                          'recompute_tangents': False, 'compute_weighted_normals': False,
                          'remove_degenerates': False}
        for name, value in final_settings.items():
            settings.set_editor_property(name, value)
        subsystem.set_lod_build_settings(mesh, 0, settings)
        assert morph_names(mesh) == old_morphs, (asset_path, old_morphs, morph_names(mesh))
        assert skeleton_signature(skeleton) == (before_skeleton, bones), 'Shared skeleton changed'
        assert animation_snapshot() == before_animations, 'Animation asset identity/skeleton/duration changed'
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        actual_settings = subsystem.get_lod_build_settings(mesh, 0)
        for name, wanted in final_settings.items():
            actual = actual_settings.get_editor_property(name)
            assert abs(actual-wanted) < 1e-10 if isinstance(wanted, float) else actual == wanted
        new_materials = materials(mesh)
        assert {n: m for n, m in new_materials} == old_by_name
        triangles = saved_asset_integer_tag(asset_path, 'Triangles')
        rows.append({'asset': asset_path, 'source_fbx': str(source), 'source_fbx_sha256': sha(source),
                     'triangles_before': old_triangles, 'source_triangles': 46249, 'saved_asset_triangles_after': triangles,
                     'original_triangle_multiplicity_exact': triangles == 46249,
                     'skeleton': skeleton.get_path_name(), 'skeleton_bones': bones,
                     'shared_skeleton_reference_unchanged': True, 'animation_assets_unchanged': True,
                     'material_bindings_preserved_by_slot_name': True, 'morph_names_preserved': True,
                     'morph_names': old_morphs, 'build_settings': final_settings,
                     'preservation_checks_pass': True})
        unreal.log('RESTORED_BODY_REIMPORT '+json.dumps(rows[-1]))
    totals = {}
    for label, prefix in [('neutral', '/Game/TLOU2/CaptureMatched1152/'),
                          ('captured', '/Game/TLOU2/CaptureMatched1152/CapturedMeshes/')]:
        totals[label] = sum(saved_asset_integer_tag(prefix+chunk+'/Ellie_Patrol_'+chunk+'_Pruned', 'Triangles')
                            for chunk in ('head_face', 'backpack', 'accessories', 'body_clothing', 'hair'))
    report = {'body_only': True, 'assets': rows, 'preservation_checks_pass': all(r['preservation_checks_pass'] for r in rows),
              'original_triangle_multiplicity_exact': all(r['original_triangle_multiplicity_exact'] for r in rows),
              'saved_asset_character_triangle_totals': totals, 'source_character_triangles': 117459,
              'runtime_reverification_required': True,
              'triangle_count_evidence': 'Saved uasset AssetRegistry FString Triangles tags. Root will additionally verify LOD0 runtime indices and captured CPU-skinned positions.',
              'pass': all(r['preservation_checks_pass'] and r['original_triangle_multiplicity_exact'] for r in rows)}
    (ROOT/'Exports/restored_body_reimport_ue_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('RESTORED_BODY_REIMPORT_RESULT '+json.dumps(report))
    if not report['original_triangle_multiplicity_exact']:
        unreal.log_warning('Importer normalized duplicate primitives; exact source FBX topology remains preserved. See report counts; no exact UE topology claim is made.')


main()
