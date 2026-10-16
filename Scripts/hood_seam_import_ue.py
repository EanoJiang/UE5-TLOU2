"""Surgical import of the source-derived seam lining into the active body mesh."""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/HoodSeam'
ASSET = '/Game/TLOU2/CaptureMatched1152/CapturedMeshes/body_clothing/Ellie_Patrol_body_clothing_Pruned'
SKELETON = '/Game/TLOU2/CaptureMatched1152/Skeleton/Ellie_CaptureMatched1152_SkeletonCarrier_Skeleton'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main(report):
    manifest = json.loads((OUT / 'repair_export.json').read_text(encoding='utf-8-sig'))
    assert manifest['pass'], manifest
    fbx = Path(manifest['fbx'])
    assert sha(fbx) == manifest['fbx_sha256']
    # Interchange preserves the original mesh's saved pipeline on reimport.
    # Use its existing asset basename so destination-name interpretation cannot
    # create an unintended second asset from the descriptive export filename.
    source_fbx = fbx
    import_dir = OUT / 'UEImport'
    import_dir.mkdir(exist_ok=True)
    fbx = import_dir / (ASSET.rsplit('/', 1)[1] + '.fbx')
    shutil.copy2(source_fbx, fbx)
    assert sha(fbx) == manifest['fbx_sha256']
    report['source_export_fbx'] = str(source_fbx)
    assert manifest['expected_body_triangles'] > 46249
    # Reuse only helper definitions. The historical script has an unconditional
    # final main() that would otherwise reimport two unrelated canonical FBXs.
    helper_path = ROOT / 'Scripts/reimport_restored_body_only_ue.py'
    prefix, excluded = helper_path.read_text().rsplit('\nmain()', 1)
    assert not excluded.strip(), 'Historical helper entry point changed'
    helper = SimpleNamespace(__name__='hood_seam_import_helpers')
    exec(compile(prefix, str(helper_path), 'exec'), helper.__dict__)
    disk = ROOT / 'Content' / (ASSET.removeprefix('/Game/') + '.uasset')
    backup = OUT / ('Backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True, exist_ok=True)
    backup_file = backup / disk.name
    shutil.copy2(disk, backup_file)
    before_sha = sha(disk)
    report.update(backup=str(backup_file), before_sha256=before_sha, fbx=str(fbx), fbx_sha256=sha(fbx))
    mesh = unreal.load_asset(ASSET)
    from editor_toolset.toolsets.asset import AssetTools
    assert not AssetTools.is_dirty(ASSET), 'Body mesh has unsaved editor changes; import stopped before modification'
    skeleton = unreal.load_asset(SKELETON)
    assert mesh.get_editor_property('skeleton') == skeleton
    before_ref = helper.skeleton_signature(skeleton)
    report['skeleton_reference_before'] = {'sha256': before_ref[0], 'bone_count': before_ref[1]}
    before_anim = helper.animation_snapshot()
    external_paths = [SKELETON, '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter',
                      '/Game/TLOU2/Blueprints/ABP_Ellie_ClothDynamics_Approx',
                      '/Game/TLOU2/Blueprints/ABP_Ellie_Face',
                      '/Game/TLOU2/Drawstring/SK_Ellie_Patrol_Drawstrings',
                      '/Game/TLOU2/Drawstring/SK_Ellie_Patrol_Drawstrings_Anim']
    external_paths += [p.split('.')[0] for p in before_anim]
    preserved_files = {str(ROOT / 'Content' / (p.removeprefix('/Game/') + '.uasset')): None for p in set(external_paths)}
    preserved_files = {p: sha(p) for p in preserved_files if Path(p).is_file()}
    from editor_toolset.toolsets.actor import ActorTools
    from editor_toolset.toolsets.blueprint import BlueprintTools
    character_bp = unreal.load_asset('/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter')
    body_template = next(c for c in ActorTools.get_components(BlueprintTools.get_default_object(character_bp))
                         if c.get_name().removesuffix('_GEN_VARIABLE') == 'SKC_BodyClothing')
    report['body_anim_class_before'] = body_template.get_editor_property('anim_class').get_path_name()
    before_materials = helper.materials(mesh)
    before_morphs = helper.morph_names(mesh)
    old_by_name = {name: mat for name, mat in before_materials}
    report['triangles_before'] = helper.saved_asset_integer_tag(ASSET, 'Triangles')
    settings_subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    before_settings = settings_subsystem.get_lod_build_settings(mesh, 0)
    preserved_settings = {name: before_settings.get_editor_property(name) for name in (
        'bone_influence_limit', 'use_high_precision_skin_weights', 'use_full_precision_u_vs',
        'use_high_precision_tangent_basis', 'morph_threshold_position', 'recompute_normals',
        'recompute_tangents', 'compute_weighted_normals', 'remove_degenerates')}
    task = unreal.AssetImportTask()
    task.filename = str(fbx)
    task.destination_path, task.destination_name = ASSET.rsplit('/', 1)
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.save = False
    options = unreal.FbxImportUI()
    for name, value in {'import_mesh': True, 'import_as_skeletal': True, 'import_animations': False,
                        'import_materials': False, 'import_textures': False, 'create_physics_asset': False,
                        'skeleton': skeleton}.items():
        options.set_editor_property(name, value)
    data = options.get_editor_property('skeletal_mesh_import_data')
    for name, value in {'import_morph_targets': True, 'morph_threshold_position': .000001,
                        'update_skeleton_reference_pose': False, 'use_t0_as_ref_pose': False,
                        'normal_import_method': unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
                        'compute_weighted_normals': False}.items():
        data.set_editor_property(name, value)
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [unreal.load_asset(p) for p in task.imported_object_paths if isinstance(unreal.load_asset(p), unreal.SkeletalMesh)]
    assert len(meshes) == 1 and meshes[0].get_path_name().split('.')[0] == ASSET
    mesh = meshes[0]
    slots = list(mesh.get_editor_property('materials'))
    assert set(str(s.get_editor_property('material_slot_name')) for s in slots) == set(old_by_name), 'Material slot identities changed'
    assert [str(s.get_editor_property('material_slot_name')) for s in slots] == [name for name, _ in before_materials], 'Material slot order changed; existing component overrides must remain aligned'
    for slot in slots:
        slot.set_editor_property('material_interface', old_by_name[str(slot.get_editor_property('material_slot_name'))])
    mesh.set_editor_property('materials', slots)
    settings = settings_subsystem.get_lod_build_settings(mesh, 0)
    for name, value in preserved_settings.items():
        settings.set_editor_property(name, value)
    settings_subsystem.set_lod_build_settings(mesh, 0, settings)
    assert mesh.get_editor_property('skeleton') == skeleton
    assert helper.skeleton_signature(skeleton) == before_ref, 'Shared reference skeleton changed'
    assert helper.animation_snapshot() == before_anim, 'Animation identity/skeleton/duration changed'
    assert helper.morph_names(mesh) == before_morphs, 'Existing corrective morph names changed'
    assert {n: m for n, m in helper.materials(mesh)} == old_by_name
    assert sha(disk) == before_sha, 'Another writer changed the body mesh before save'
    assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    triangles_after = helper.saved_asset_integer_tag(ASSET, 'Triangles')
    assert triangles_after == manifest['expected_body_triangles'], (triangles_after, manifest['expected_body_triangles'])
    assert all(sha(path) == value for path, value in preserved_files.items()), 'An external asset changed during the mesh-only import'
    report.update(asset=mesh.get_path_name(), after_sha256=sha(disk), triangles_after=triangles_after,
                  added_triangles=triangles_after-report['triangles_before'], skeleton_reference_unchanged=True,
                  animation_metadata_unchanged=True, material_bindings_unchanged=True,
                  corrective_morphs=before_morphs, mesh_build_settings=preserved_settings,
                  existing_blueprint_or_level_writes=False, external_asset_hashes_preserved=preserved_files)
    if globals().get('HOOD_SEAM_SKIP_DIAGNOSTIC', False):
        report['live_editor_current_level_preserved'] = True
        report['pass'] = True
        return
    # Isolated diagnostic level reuses the project's native CPU skin audit.
    diagnostic = '/Game/TLOU2/HoodSeam/Diagnostics/BodyVertexAudit'
    assert unreal.EditorLevelLibrary.new_level(diagnostic)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode', unreal.load_class(None, '/Script/TLOU2Codex.CatalogGameMode'))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label('HoodSeam_BodyVertexAudit')
    actor.set_editor_property('tags', ['CaptureAffineCorrective'])
    component = actor.skeletal_mesh_component
    component.set_editor_property('skeletal_mesh_asset', mesh)
    component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    animation = unreal.load_asset('/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim')
    animation_data = component.get_editor_property('animation_data')
    for key, value in {'anim_to_play': animation, 'saved_playing': True, 'saved_looping': True,
                       'saved_position': 0., 'saved_play_rate': 1.}.items():
        animation_data.set_editor_property(key, value)
    component.set_editor_property('animation_data', animation_data)
    component.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report['isolated_diagnostic_map'] = diagnostic
    report['pass'] = True

report = {'pass': False}
try:
    main(report)
except Exception:
    report['error'] = traceback.format_exc()
    raise
finally:
    (OUT / 'ue_import.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('HOOD_SEAM_IMPORT ' + json.dumps(report))
