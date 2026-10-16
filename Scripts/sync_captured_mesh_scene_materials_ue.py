"""Copy scene-effective material references into existing captured mesh slots.

Run in the current editor or in a Python commandlet. Commandlets load the saved
catalog map; interactive execution uses the current editor world. Add
-SceneMaterialSyncVerify for independent disk-read verification, without saves.
"""
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
TARGET = '/Game/TLOU2/CaptureMatched1152/CapturedMeshes'
MAP = '/Game/TLOU2/Maps/ElliePatrolCaptureMatched'
APPLICATION = ROOT/'Exports/captured_mesh_scene_material_sync_application.json'
VALIDATION = ROOT/'Exports/captured_mesh_scene_material_sync_validation.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def asset_file(mesh_path):
    package = mesh_path.split('.')[0]
    assert package.startswith(TARGET+'/')
    return ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset')


def path_of(obj):
    return obj.get_path_name() if obj else None


def slot_metadata(slot):
    # MaterialInterface is the only field this task changes. Retain every other
    # reflected FSkeletalMaterial field, including imported names and UV data.
    text = slot.export_text()
    return re.sub(r'(?<=[(,])MaterialInterface=[^,)]*,?', '', text).replace('(,', '(').replace(',)', ')')


def mesh_state(mesh):
    slots = mesh.get_editor_property('materials')
    subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    return {'skeleton': path_of(mesh.get_editor_property('skeleton')),
            'slots': [slot_metadata(slot) for slot in slots],
            'lod_info': [subsystem.get_lod_build_settings(mesh, index).export_text()
                         for index in range(subsystem.get_lod_count(mesh))],
            'morphs': sorted(item.get_name() for item in mesh.get_editor_property('morph_targets'))}


def target_meshes():
    result = {}
    for path in unreal.EditorAssetLibrary.list_assets(TARGET, recursive=True, include_folder=False):
        mesh = unreal.load_asset(path)
        if isinstance(mesh, unreal.SkeletalMesh):
            result[mesh.get_path_name()] = mesh
    assert len(result) == 5, ('Unexpected captured mesh selection', list(result))
    return result


def verify():
    application = json.loads(APPLICATION.read_text(encoding='utf-8'))
    meshes = target_meshes()
    assert set(meshes) == {row['mesh'] for row in application['meshes']}
    rows = []
    for source in application['meshes']:
        mesh = meshes[source['mesh']]
        actual = [path_of(slot.get_editor_property('material_interface')) for slot in mesh.get_editor_property('materials')]
        state = mesh_state(mesh)
        file_hash = sha(asset_file(mesh.get_path_name()))
        ok = actual == source['scene_materials'] and state == source['state_before'] and file_hash == source['saved_asset_sha256']
        rows.append({'mesh': mesh.get_path_name(), 'material_slots': len(actual),
                     'scene_materials': source['scene_materials'], 'saved_mesh_materials': actual,
                     'slot_metadata_skeleton_lods_morphs_preserved': state == source['state_before'],
                     'saved_asset_sha256': file_hash, 'pass': ok})
    report = {'pass': all(row['pass'] for row in rows), 'mesh_count': len(rows),
              'material_slots': sum(row['material_slots'] for row in rows),
              'application_sha256': sha(APPLICATION), 'source_world': application['source_world'],
              'source_policy': application['source_policy'],
              'method': 'Fresh UE process reads saved SkeletalMesh defaults and compares exact material object paths at every numeric slot with the captured scene snapshot. No asset or map is saved by this verification.',
              'meshes': rows}
    VALIDATION.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('CAPTURED_MESH_SCENE_MATERIAL_VERIFY '+json.dumps({k:v for k,v in report.items() if k != 'meshes'}))
    assert report['pass'] and report['material_slots'] == 24


def apply():
    command_line = unreal.SystemLibrary.get_command_line().casefold()
    is_commandlet = '-run=pythonscript' in command_line
    if is_commandlet:
        assert unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    meshes = target_meshes()
    plans = {}
    components = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_editor_property('skeletal_mesh')
            if not mesh or mesh.get_path_name() not in meshes:
                continue
            slots = mesh.get_editor_property('materials')
            assert component.get_num_materials() == len(slots), ('Scene/asset slot count differs', component.get_path_name())
            materials = [component.get_material(index) for index in range(len(slots))]
            assert all(isinstance(material, unreal.MaterialInterface) and not isinstance(material, unreal.MaterialInstanceDynamic)
                       and material.get_path_name().startswith('/Game/') for material in materials), 'Expected persistent material asset references'
            paths = [path_of(material) for material in materials]
            key = mesh.get_path_name()
            if key in plans:
                assert plans[key]['scene_materials'] == paths, ('Conflicting scene instance materials', key)
                plans[key]['source_components'].append(component.get_path_name())
            else:
                plans[key] = {'mesh': key, 'scene_materials': paths, 'materials': materials,
                              'source_components': [component.get_path_name()], 'state_before': mesh_state(mesh)}
            components.append((component, paths, [path_of(m) for m in component.get_editor_property('override_materials')]))
    assert set(plans) == set(meshes), ('Scene does not cover every target mesh', set(meshes)-set(plans))
    assert sum(len(row['materials']) for row in plans.values()) == 24
    map_file = ROOT/'Content/TLOU2/Maps/ElliePatrolCaptureMatched.umap'
    map_sha = sha(map_file)
    backup = ROOT/'Exports/SceneMaterialSyncBackup'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    rows = []
    for key, plan in plans.items():
        mesh = meshes[key]
        slots = mesh.get_editor_property('materials')
        before = [path_of(slot.get_editor_property('material_interface')) for slot in slots]
        changed = [index for index, (a,b) in enumerate(zip(before, plan['scene_materials'])) if a != b]
        file = asset_file(key)
        original_hash = sha(file)
        if changed:
            destination = backup/file.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, destination)
            for index in changed:
                slot = slots[index]
                slot.set_editor_property('material_interface', plan['materials'][index])
                slots[index] = slot
            mesh.set_editor_property('materials', slots)
            assert mesh_state(mesh) == plan['state_before'], ('Unexpected non-material changes', key)
            assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), ('Save failed', key)
        actual = [path_of(slot.get_editor_property('material_interface')) for slot in mesh.get_editor_property('materials')]
        assert actual == plan['scene_materials'], (key, actual, plan['scene_materials'])
        rows.append({k:v for k,v in plan.items() if k != 'materials'} | {
            'asset_materials_before': before, 'changed_slots': changed, 'original_asset_sha256': original_hash,
            'saved_asset_sha256': sha(file), 'pass': True})
    for component, paths, overrides in components:
        assert [path_of(component.get_material(i)) for i in range(len(paths))] == paths
        assert [path_of(m) for m in component.get_editor_property('override_materials')] == overrides
    assert sha(map_file) == map_sha
    report = {'pass': True, 'target': TARGET, 'source_world': world.get_path_name(),
              'source_policy': 'Saved canonical catalog map loaded by commandlet' if is_commandlet else 'Current live editor world',
              'mesh_count': len(rows), 'material_slots': sum(len(row['scene_materials']) for row in rows),
              'changed_material_slots': sum(len(row['changed_slots']) for row in rows),
              'scene_override_arrays_unchanged': True, 'map_file_sha256_unchanged': map_sha,
              'backup_directory': str(backup), 'meshes': rows}
    APPLICATION.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('CAPTURED_MESH_SCENE_MATERIAL_APPLY '+json.dumps({k:v for k,v in report.items() if k != 'meshes'}))


if '-scenematerialsyncverify' in unreal.SystemLibrary.get_command_line().casefold():
    verify()
else:
    apply()
