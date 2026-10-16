"""Read-only fresh-process checks after the mesh-only seam import."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/HoodSeam'
ASSET = '/Game/TLOU2/CaptureMatched1152/CapturedMeshes/body_clothing/Ellie_Patrol_body_clothing_Pruned'
imported = json.loads((OUT / 'ue_import.json').read_text(encoding='utf-8-sig'))
exported = json.loads((OUT / 'repair_export.json').read_text(encoding='utf-8-sig'))
helper_path = ROOT / 'Scripts/reimport_restored_body_only_ue.py'
prefix, excluded = helper_path.read_text().rsplit('\nmain()', 1)
assert not excluded.strip()
helper = SimpleNamespace(__name__='hood_seam_verify_helpers')
exec(compile(prefix, str(helper_path), 'exec'), helper.__dict__)
checks, details = {}, {}
success, spawned = False, None
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    mesh = unreal.load_asset(ASSET)
    checks['mesh_saved_at_original_path'] = bool(mesh) and imported['asset'] == mesh.get_path_name()
    checks['saved_body_triangle_count'] = helper.saved_asset_integer_tag(ASSET, 'Triangles') == exported['expected_body_triangles']
    skeleton = mesh.get_editor_property('skeleton')
    signature, count = helper.skeleton_signature(skeleton)
    checks['shared_skeleton_reference_preserved'] = signature == imported['skeleton_reference_before']['sha256'] and count == imported['skeleton_reference_before']['bone_count']
    checks['corrective_morphs_preserved'] = helper.morph_names(mesh) == imported['corrective_morphs']
    checks['external_assets_unchanged'] = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path, value in imported['external_asset_hashes_preserved'].items())
    settings = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem).get_lod_build_settings(mesh, 0)
    checks['mesh_settings_preserved'] = all(settings.get_editor_property(name) == value for name, value in imported['mesh_build_settings'].items())
    checks['correct_source_fbx'] = Path(mesh.get_editor_property('asset_import_data').get_first_filename()).resolve() == Path(imported['fbx']).resolve() and hashlib.sha256(Path(imported['fbx']).read_bytes()).hexdigest() == exported['fbx_sha256']
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level('/Game/TLOU2/Maps/ElliePatrolCaptureGroomFront')
    cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter')
    placed = [a for a in actors.get_all_level_actors() if a.get_class() == cls]
    assert len(placed) == 1
    spawned = actors.spawn_actor_from_class(cls, unreal.Vector(), unreal.Rotator())
    for label, actor in [('placed', placed[0]), ('fresh_spawn', spawned)]:
        comps = {c.get_name(): c for c in actor.get_components_by_class(unreal.SkeletalMeshComponent)}
        body = comps['SKC_BodyClothing']
        checks[label+'_uses_patched_body'] = body.get_editor_property('skeletal_mesh_asset') == mesh
        checks[label+'_drawstrings_preserved'] = 'SKC_Drawstrings' in comps and comps['SKC_Drawstrings'].is_visible()
        checks[label+'_body_anim_class_preserved'] = body.get_editor_property('anim_class').get_path_name() == imported['body_anim_class_before']
        details[label] = {'body': body.get_path_name(), 'animation_blueprint': body.get_editor_property('anim_class').get_path_name(),
                          'drawstring_mesh': comps['SKC_Drawstrings'].get_editor_property('skeletal_mesh_asset').get_path_name()}
    assert all(checks.values()), checks
    success = True
finally:
    if spawned:
        actors.destroy_actor(spawned)
    report = {'pass': success and all(checks.values()), 'checks': checks, 'details': details,
              'method': 'Fresh UE process; saved mesh count/reference/morph/build settings and unchanged external hashes, existing map instance and fresh blueprint spawn; no saves'}
    (OUT / 'ue_saved_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('HOOD_SEAM_SAVED_VERIFY ' + json.dumps(report))
