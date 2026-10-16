"""Persist Ellie captured-pose Groom as an SCS default, keeping animation intact.

Run with UnrealEditor-Cmd -run=pythonscript. The editor must be closed so the
physical pre-edit package backups also contain the complete authoritative state.
"""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path

import unreal
from editor_toolset.toolsets.actor import ActorTools
from editor_toolset.toolsets.asset import AssetTools
from editor_toolset.toolsets.blueprint import BlueprintTools

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom/BlueprintIntegration'
BP_PATH = '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter'
GROOM_PATH = '/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom'
MATERIAL_PATH = '/Game/TLOU2/Groom/M_Ellie_CaptureGroom_Hair'
ANIM_PATH = '/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim'
MAPS = ['/Game/TLOU2/Maps/' + name for name in (
    'ElliePatrolCaptureGroom', 'ElliePatrolCaptureGroomFront',
    'ElliePatrolCaptureGroomThreeQuarter', 'ElliePatrolCaptureGroomBack',
    'ElliePatrolCaptureMatched')]
NAME = 'Groom_Hair'
ANCHOR_NAME = 'SC_GroomHeadAnchor'
HEAD_NAME = 'SKC_HeadFace'
BONE = 'headb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def trans(t):
    return {'translation': vec(t.translation), 'rotation_xyzw': [float(t.rotation.x),
            float(t.rotation.y), float(t.rotation.z), float(t.rotation.w)],
            'scale': vec(t.scale3d)}


def ref(obj):
    return obj.get_path_name() if obj else None


def templates(bp):
    return {c.get_name().removesuffix('_GEN_VARIABLE'): c for c in
            ActorTools.get_components(BlueprintTools.get_default_object(bp))}


def skeleton_snapshot(component):
    return {key: ref(component.get_editor_property(key)) if key in
            ('skeletal_mesh_asset', 'anim_class') else str(component.get_editor_property(key))
            for key in ('skeletal_mesh_asset', 'anim_class', 'animation_mode',
                        'animation_data', 'relative_location', 'relative_rotation',
                        'relative_scale3d')}


def describe_groom(c):
    return {'path': ref(c), 'groom_asset': ref(c.get_editor_property('groom_asset')),
            'binding_asset': ref(c.get_editor_property('binding_asset')),
            'use_cards': c.get_editor_property('use_cards'),
            'groom_attachment_name': str(c.get_editor_property('attachment_name')),
            'socket': str(c.get_attach_socket_name()),
            'parent': ref(c.get_attach_parent()),
            'relative_transform': trans(c.get_relative_transform()),
            'visible': c.is_visible(), 'hidden_in_game': c.get_editor_property('hidden_in_game'),
            'simulation_override': c.get_editor_property('simulation_settings').get_editor_property('override_settings'),
            'simulation_enabled': c.get_editor_property('simulation_settings').get_editor_property('solver_settings').get_editor_property('enable_simulation'),
            'materials': [ref(c.get_material(i)) for i in range(c.get_num_materials())]}


def disable_simulation(c):
    settings = c.get_editor_property('simulation_settings')
    settings.set_editor_property('override_settings', True)
    solver = settings.get_editor_property('solver_settings')
    solver.set_editor_property('enable_simulation', False)
    settings.set_editor_property('solver_settings', solver)
    c.set_editor_property('simulation_settings', settings)
    c.set_enable_simulation(False)


def assert_blank_attachment(c):
    value = c.get_editor_property('attachment_name')
    assert isinstance(value, str) and value == '', (type(value).__name__, repr(value))


def describe_anchor(c):
    return {'path': ref(c), 'socket': str(c.get_attach_socket_name()),
            'parent': ref(c.get_attach_parent()),
            'relative_transform': trans(c.get_relative_transform())}


def main(report):
    OUT.mkdir(parents=True, exist_ok=True)
    previous_path = OUT / 'integration_result.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.is_file() else {}
    previous_maps = {row['map']: row for row in previous.get('maps', [])} if previous.get('pass') else {}
    if previous.get('pass'):
        shutil.copy2(previous_path, OUT / ('integration_previous_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json'))
    backup_dir = OUT / ('Backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup_dir.mkdir()
    report['backups'] = []
    report['maps_absent_before_integration'] = []
    existing_maps = []
    for asset_path in [BP_PATH] + MAPS:
        extension = '.umap' if '/Maps/' in asset_path else '.uasset'
        source = ROOT / 'Content' / (asset_path.removeprefix('/Game/') + extension)
        if not source.is_file() and asset_path in MAPS:
            report['maps_absent_before_integration'].append(asset_path)
            continue
        assert source.is_file(), str(source)
        if asset_path in MAPS:
            existing_maps.append(asset_path)
        target = backup_dir / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        original_backup = next(p / source.relative_to(ROOT) for p in sorted(OUT.glob('Backup_*'))
                               if (p / source.relative_to(ROOT)).is_file())
        report['backups'].append({'asset': asset_path, 'source': str(source),
                                  'backup': str(target), 'sha256_before': sha(source),
                                  'original_backup': str(original_backup),
                                  'original_sha256': sha(original_backup)})

    bp = unreal.load_asset(BP_PATH)
    assert isinstance(bp, unreal.Blueprint), BP_PATH
    report['initial_dirty'] = {p: AssetTools.is_dirty(p) for p in [BP_PATH] + existing_maps}
    # No user-owned in-memory changes exist: this process started after the live
    # editor had cleanly exited. Do not overwrite a package made dirty by loading.
    assert not any(report['initial_dirty'].values()), report['initial_dirty']
    original = templates(bp)
    assert all(n in original for n in (HEAD_NAME, 'SKC_Hair', 'SKC_Accessories',
                                        'SKC_BodyClothing', 'SKC_Backpack')), list(original)
    report['skeleton_before'] = {n: skeleton_snapshot(c) for n, c in original.items()
                                  if isinstance(c, unreal.SkeletalMeshComponent)}
    report['original_source_hair_defaults'] = {
        n: {'visible': original[n].is_visible(),
            'hidden_in_game': original[n].get_editor_property('hidden_in_game')}
        for n in ('SKC_Hair', 'SKC_Accessories')}
    head = original[HEAD_NAME]
    head_mesh = head.get_editor_property('skeletal_mesh_asset')
    assert head_mesh.get_path_name().startswith(
        '/Game/TLOU2/CaptureMatched1152/CapturedMeshes/head_face/Ellie_Patrol_head_face_Pruned'), ref(head_mesh)
    anim = unreal.load_asset(ANIM_PATH)
    opts = unreal.AnimPoseEvaluationOptions()
    opts.set_editor_property('evaluation_type', unreal.AnimDataEvalType.COMPRESSED)
    opts.set_editor_property('should_retarget', True)
    opts.set_editor_property('extract_root_motion', False)
    opts.set_editor_property('optional_skeletal_mesh', head_mesh)
    pose = anim.get_anim_pose_at_frame(0, opts)
    assert pose.is_valid() and BONE in [str(n) for n in pose.get_bone_names()]
    anim_captured = pose.get_bone_pose(BONE, unreal.AnimPoseSpaces.WORLD)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    probe = actors.spawn_actor_from_class(bp.generated_class(), unreal.Vector())
    probe_head = next(c for c in probe.get_components_by_class(unreal.SkeletalMeshComponent)
                      if c.get_name() == HEAD_NAME)
    assert probe_head.get_bone_index(BONE) == 8
    captured = probe_head.get_socket_transform(BONE, unreal.RelativeTransformSpace.RTS_COMPONENT)
    relative = captured.inverse()
    assert actors.destroy_actor(probe)
    report['attachment'] = {'head_component': HEAD_NAME, 'head_mesh': ref(head_mesh),
        'socket': BONE, 'captured_head_transform': trans(captured),
        'compressed_animpose_head_transform': trans(anim_captured),
        'relative_transform': trans(relative),
        'anchor_component': ANCHOR_NAME,
        'policy': 'SCS SceneComponent anchor on headb with inverse captured bone transform; identity Groom child avoids the direct skeletal parent rigid transform; no skin binding or simulation'}
    # Native Transform composition check prevents a 100x imported skeleton scale
    # from changing this groom, which is authored directly in component-space cm.
    neutral = unreal.MathLibrary.compose_transforms(relative, captured)
    assert max(abs(v) for v in vec(neutral.translation)) < .001, trans(neutral)
    assert max(abs(v - 1) for v in vec(neutral.scale3d)) < .00001, trans(neutral)

    if ANCHOR_NAME not in original:
        ActorTools.add_component(head, unreal.SceneComponent.static_class(), ANCHOR_NAME)
    components = templates(bp)
    anchor = components[ANCHOR_NAME]
    if NAME in components:
        groom = components[NAME]
        assert isinstance(groom, unreal.GroomComponent)
        assert ActorTools.set_parent_component(groom, anchor)
    else:
        groom = ActorTools.add_component(anchor, unreal.GroomComponent.static_class(), NAME)
    # Compile performed by add_component can reinstance templates. Resolve them.
    components = templates(bp)
    groom = components[NAME]
    head = components[HEAD_NAME]
    anchor = components[ANCHOR_NAME]
    assert unreal.GroomBlueprintEditorLibrary.set_blueprint_component_socket(bp, anchor, BONE)
    anchor.modify()
    anchor.set_editor_property('relative_location', relative.translation)
    anchor.set_editor_property('relative_rotation', relative.rotation.rotator())
    anchor.set_editor_property('relative_scale3d', relative.scale3d)
    anchor.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    assert unreal.GroomBlueprintEditorLibrary.set_blueprint_component_socket(bp, groom, unreal.Name())
    groom.modify()
    groom.set_editor_property('relative_location', unreal.Vector())
    groom.set_editor_property('relative_rotation', unreal.Rotator())
    groom.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
    groom.set_editor_property('attachment_name', '')
    groom.set_editor_property('binding_asset', None)
    groom.set_editor_property('use_cards', False)
    groom.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    groom.set_visibility(True, False)
    groom.set_hidden_in_game(False, False)
    asset = unreal.load_asset(GROOM_PATH)
    material = unreal.load_asset(MATERIAL_PATH)
    assert isinstance(asset, unreal.GroomAsset) and isinstance(material, unreal.MaterialInterface)
    groom.set_groom_asset(None)
    groom.set_groom_asset(asset)
    disable_simulation(groom)
    for index in range(max(1, groom.get_num_materials())):
        groom.set_material(index, material)
    for n in ('SKC_Hair', 'SKC_Accessories'):
        c = components[n]
        c.modify()
        c.set_visibility(False, False)
        c.set_hidden_in_game(True, False)
    bp.modify()
    BlueprintTools.compile_blueprint(bp, warnings_as_errors=True)
    after = templates(bp)
    assert_blank_attachment(after[NAME])
    report['skeleton_after'] = {n: skeleton_snapshot(after[n]) for n in report['skeleton_before']}
    assert report['skeleton_before'] == report['skeleton_after'], 'Mesh or animation configuration changed'
    report['blueprint_component'] = describe_groom(after[NAME])
    report['blueprint_anchor'] = describe_anchor(after[ANCHOR_NAME])
    report['scs_node'] = json.loads(unreal.GroomBlueprintEditorLibrary.describe_blueprint_component_attachment(bp, after[NAME]))
    report['anchor_scs_node'] = json.loads(unreal.GroomBlueprintEditorLibrary.describe_blueprint_component_attachment(bp, after[ANCHOR_NAME]))
    assert report['scs_node']['parent_component'] == ANCHOR_NAME + '_GEN_VARIABLE', report['scs_node']
    assert report['scs_node']['attach_to_name'] == 'None', report['scs_node']
    assert report['anchor_scs_node']['parent_component'] == HEAD_NAME + '_GEN_VARIABLE', report['anchor_scs_node']
    assert report['anchor_scs_node']['attach_to_name'] == BONE, report['anchor_scs_node']
    report['source_hair_defaults'] = {n: {'visible': after[n].is_visible(),
        'hidden_in_game': after[n].get_editor_property('hidden_in_game')} for n in ('SKC_Hair', 'SKC_Accessories')}
    assert all(not row['visible'] and row['hidden_in_game'] for row in report['source_hair_defaults'].values())
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    report['blueprint_saved'] = True
    report['blueprint_compile_status'] = str(bp.get_editor_property('status'))

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    report['maps'] = []
    for path in existing_maps:
        assert levels.load_level(path), path
        # Loading serialized placed actors does not rerun their SCS in a
        # commandlet. Reinstancing after the map is resident adds new defaults.
        BlueprintTools.compile_blueprint(bp, warnings_as_errors=True)
        removed = []
        for actor in list(actors.get_all_level_actors()):
            if not isinstance(actor, unreal.GroomActor):
                continue
            component = actor.get_component_by_class(unreal.GroomComponent)
            if component and ref(component.get_editor_property('groom_asset')) == ref(asset):
                removed.append({'path': ref(actor), 'label': actor.get_actor_label()})
                assert actors.destroy_actor(actor)
        characters = [a for a in actors.get_all_level_actors() if a.get_class() == bp.generated_class()]
        assert len(characters) == 1, (path, [ref(a) for a in characters])
        character = characters[0]
        grooms = list(character.get_components_by_class(unreal.GroomComponent))
        assert len(grooms) == 1, (path, [ref(c) for c in grooms])
        c = grooms[0]
        assert c.get_attach_parent().get_name() == ANCHOR_NAME, describe_groom(c)
        placed_anchor = c.get_attach_parent()
        assert placed_anchor.get_attach_parent().get_name() == HEAD_NAME and str(placed_anchor.get_attach_socket_name()) == BONE, describe_anchor(placed_anchor)
        placed_anchor.set_editor_property('relative_location', relative.translation)
        placed_anchor.set_editor_property('relative_rotation', relative.rotation.rotator())
        placed_anchor.set_editor_property('relative_scale3d', relative.scale3d)
        c.set_editor_property('relative_location', unreal.Vector())
        c.set_editor_property('relative_rotation', unreal.Rotator())
        c.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
        # Refresh render resources for any archetype-updated existing instance.
        c.set_groom_asset(None)
        c.set_groom_asset(asset)
        c.set_editor_property('attachment_name', '')
        assert_blank_attachment(c)
        disable_simulation(c)
        cards = [x for x in character.get_components_by_class(unreal.SkeletalMeshComponent)
                 if x.get_name() in ('SKC_Hair', 'SKC_Accessories')]
        assert len(cards) == 2
        # Existing preview maps can contain old instance overrides; persist the
        # same source-card visibility on those while the BP defaults cover spawns.
        for card in cards:
            card.set_visibility(False, False)
            card.set_hidden_in_game(True, False)
        assert levels.save_current_level(), path
        previous_row = previous_maps.get(path, {})
        report['maps'].append({'map': path, 'removed_count': len(removed) + previous_row.get('removed_count', 0),
            'removed_this_run': len(removed),
            'removed': previous_row.get('removed', []) + removed,
            'character': ref(character), 'groom': describe_groom(c), 'anchor': describe_anchor(placed_anchor),
            'standalone_groom_count_after': sum(isinstance(a, unreal.GroomActor) for a in actors.get_all_level_actors()),
            'saved': True})
    for row in report['backups']:
        row['sha256_after'] = sha(Path(row['source']))
    report['pass'] = True


def correct_attachment_string(report):
    """Correct the FString field without obscuring the original removal audit."""
    bp = unreal.load_asset(BP_PATH)
    c = templates(bp)[NAME]
    correction = {'before_default': repr(c.get_editor_property('attachment_name')), 'maps': []}
    c.modify()
    c.set_editor_property('attachment_name', '')
    BlueprintTools.compile_blueprint(bp, warnings_as_errors=True)
    c = templates(bp)[NAME]
    assert_blank_attachment(c)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    correction['after_default'] = repr(c.get_editor_property('attachment_name'))
    correction['native_property_type'] = type(c.get_editor_property('attachment_name')).__name__
    report['blueprint_component'] = describe_groom(c)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for row in report['maps']:
        assert levels.load_level(row['map']), row['map']
        BlueprintTools.compile_blueprint(bp, warnings_as_errors=True)
        character = next(a for a in actors.get_all_level_actors() if a.get_class() == bp.generated_class())
        c = character.get_component_by_class(unreal.GroomComponent)
        before = repr(c.get_editor_property('attachment_name'))
        c.modify()
        c.set_editor_property('attachment_name', '')
        assert_blank_attachment(c)
        assert levels.save_current_level(), row['map']
        row['groom'] = describe_groom(c)
        correction['maps'].append({'map': row['map'], 'before': before,
                                   'after': repr(c.get_editor_property('attachment_name')), 'saved': True})
    for row in report['backups']:
        row['sha256_after'] = sha(Path(row['source']))
    report['attachment_string_correction'] = correction
    report['pass'] = True


report = {'pass': False, 'blueprint': BP_PATH, 'groom': GROOM_PATH, 'component_name': NAME,
          'material': MATERIAL_PATH, 'method': 'Offline UnrealEditor-Cmd native SCS default creation after editor clean shutdown',
          'simulation': False, 'skin_binding': False}
try:
    if '-GroomAttachmentBlankCorrection' in unreal.SystemLibrary.get_command_line():
        report = json.loads((OUT / 'integration_result.json').read_text(encoding='utf-8'))
        assert report['pass']
        correct_attachment_string(report)
    else:
        main(report)
except Exception as exc:
    report['pass'] = False
    report['error'] = str(exc)
    report['traceback'] = traceback.format_exc()
    unreal.log_error('GROOM_BP_INTEGRATION_ERROR ' + report['traceback'])
    raise
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'integration_result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('GROOM_BP_INTEGRATION ' + json.dumps(report))
