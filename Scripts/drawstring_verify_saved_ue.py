"""Fresh-process verification of inherited strings, owned rig and attachment."""
import json
import math
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Drawstring'
BP = '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter'
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
checks, details, spawned = {}, {}, None
success = False

def xyz(v):
    return [float(v.x), float(v.y), float(v.z)]

def points(c):
    t = c.get_world_transform()
    return [xyz(unreal.MathLibrary.transform_location(t, unreal.Vector(*p))) for p in ((0, 0, 138), (5, 0, 138), (0, 5, 138))]

def err(a, b):
    return max(abs(x-y) for pa, pb in zip(a, b) for x, y in zip(pa, pb))

try:
    assert levels.load_level('/Game/TLOU2/Maps/ElliePatrolCaptureGroom')
    cls = unreal.EditorAssetLibrary.load_blueprint_class(BP)
    spawned = actors.spawn_actor_from_class(cls, unreal.Vector(), unreal.Rotator())
    strings = [c for c in spawned.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'SKC_Drawstrings']
    checks['fresh_instance_one_drawstring_component'] = len(strings) == 1
    assert checks['fresh_instance_one_drawstring_component'], 'Expected saved strings component on new instance'
    c = strings[0]
    mesh = c.get_editor_property('skeletal_mesh_asset')
    data = c.get_editor_property('animation_data')
    anim = data.get_editor_property('anim_to_play')
    material = c.get_material(0)
    checks['private_original_mesh'] = mesh.get_path_name().startswith('/Game/TLOU2/Drawstring/SK_Ellie_Patrol_Drawstrings.')
    checks['visible'] = c.is_visible() and not c.get_editor_property('hidden_in_game')
    checks['independent_captured_animation'] = isinstance(anim, unreal.AnimSequence) and anim.get_path_name().startswith('/Game/TLOU2/Drawstring/') and anim.get_skeleton() == mesh.get_editor_property('skeleton')
    checks['single_node_animation'] = c.get_editor_property('animation_mode') == unreal.AnimationMode.ANIMATION_SINGLE_NODE
    checks['material_bound'] = material.get_path_name().startswith('/Game/TLOU2/Drawstring/M_Ellie_Patrol_Drawstrings.')
    morphs = [m.get_name() for m in mesh.get_editor_property('morph_targets') if 'CaptureAffineCorrective' in m.get_name()]
    checks['corrective_morph_exists'] = bool(morphs)
    curve_samples = {name: [unreal.AnimationLibrary.get_float_value_at_time(anim, name, t) for t in (0., anim.get_play_length()/2., anim.get_play_length())] for name in morphs}
    checks['corrective_curves_persisted'] = bool(curve_samples) and all(abs(v-1.) < 1e-6 for values in curve_samples.values() for v in values)
    details['morph_curve_samples'] = curve_samples
    names = [r['bone_name'] for r in json.loads((OUT / 'owned_rig22.json').read_text())['rows']]
    checks['all22_owned_bones_preserved'] = all(c.get_bone_index(n) >= 0 for n in names)
    build = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem).get_lod_build_settings(mesh, 0)
    checks['eight_influences_enabled'] = build.get_editor_property('bone_influence_limit') >= 8
    checks['high_precision_weights'] = build.get_editor_property('use_high_precision_skin_weights')
    chain, child, body = [], c, None
    while child.get_attach_parent():
        parent = child.get_attach_parent()
        chain.append({'child': child.get_name(), 'parent': parent.get_name(), 'socket': str(child.get_attach_socket_name())})
        if parent.get_name() == 'SKC_BodyClothing' and str(child.get_attach_socket_name()) == 'spined':
            body = parent
        child = parent
    checks['chest_socket_attachment'] = body is not None
    details['attachment_chain'] = chain
    before = points(c)
    shift = unreal.Vector(123, -47, 18)
    spawned.set_actor_location(shift, False, False)
    expected = [[p[0]+shift.x, p[1]+shift.y, p[2]+shift.z] for p in before]
    checks['actor_translation_follows'] = err(points(c), expected) < .002
    yaw = 37.
    spawned.set_actor_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0), False)
    cs, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    expected = [[p[0]*cs-p[1]*sn+shift.x, p[0]*sn+p[1]*cs+shift.y, p[2]+shift.z] for p in before]
    checks['actor_rotation_follows'] = err(points(c), expected) < .002
    if body:
        old = body.get_editor_property('relative_location')
        previous = points(c)
        body.set_relative_location(old+unreal.Vector(5, 0, 0), False, False)
        checks['body_component_motion_follows'] = math.dist(points(c)[0], previous[0]) > 4.9
        body.set_relative_location(old, False, False)
    details.update(mesh=mesh.get_path_name(), animation=anim.get_path_name(), material=material.get_path_name(), bone_count=c.get_num_bones())
    actors.destroy_actor(spawned)
    spawned = None
    details['maps'] = []
    for asset in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Maps', recursive=False, include_folder=False):
        if 'ElliePatrolCaptureGroom' not in asset:
            continue
        assert levels.load_level(asset.split('.')[0]), asset
        row = {'map': asset, 'characters': []}
        for actor in actors.get_all_level_actors():
            if actor.get_class() == cls:
                components = [comp for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent) if comp.get_name() == 'SKC_Drawstrings']
                checks[asset+'_strings'] = len(components) == 1 and components[0].is_visible()
                row['characters'].append(actor.get_path_name())
        checks[asset+'_has_character'] = bool(row['characters'])
        details['maps'].append(row)
    assert all(checks.values()), checks
    success = True
finally:
    if spawned:
        actors.destroy_actor(spawned)
    report = {'pass': success and bool(checks) and all(checks.values()), 'checks': checks, 'details': details,
              'method': 'Fresh UE process, saved blueprint class, fresh spawn, original22 bone names, animation/material, inherited saved-map components and motion propagation'}
    (OUT / 'ue_saved_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('DRAWSTRING_SAVED_VERIFY ' + json.dumps(report))
