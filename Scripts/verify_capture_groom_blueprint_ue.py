"""Fresh-process checks for Blueprint-owned hair, attachment and instance motion."""
import json
import math
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom/BlueprintIntegration'
OUT.mkdir(parents=True, exist_ok=True)
BP = '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter'
MAPS = ['ElliePatrolCaptureGroom',
        'ElliePatrolCaptureGroomFront', 'ElliePatrolCaptureGroomThreeQuarter',
        'ElliePatrolCaptureGroomBack']
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
checks, details, spawned = {}, {}, None

def xyz(v):
    return [float(v.x), float(v.y), float(v.z)]

def points(component):
    transform = component.get_world_transform()
    return [xyz(unreal.MathLibrary.transform_location(transform, unreal.Vector(*p)))
            for p in ((0, 0, 155), (10, 0, 155), (0, 10, 155))]

def maximum_error(a, b):
    return max(abs(x - y) for pa, pb in zip(a, b) for x, y in zip(pa, pb))

try:
    assert levels.load_level('/Game/TLOU2/Maps/ElliePatrolCaptureGroom')
    cls = unreal.EditorAssetLibrary.load_blueprint_class(BP)
    assert cls, BP
    spawned = actors.spawn_actor_from_class(cls, unreal.Vector(), unreal.Rotator())
    grooms = list(spawned.get_components_by_class(unreal.GroomComponent))
    checks['fresh_spawn_has_one_groom_component'] = len(grooms) == 1
    assert checks['fresh_spawn_has_one_groom_component'], 'New Blueprint instance has %d GroomComponents' % len(grooms)
    groom = grooms[0]
    checks['groom_owned_by_character'] = groom.get_owner() == spawned
    checks['correct_groom_asset'] = groom.get_editor_property('groom_asset').get_path_name() == '/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom.Ellie_Patrol_CaptureGroom'
    checks['strands_visible'] = groom.is_visible() and not groom.get_editor_property('use_cards')
    checks['groom_internal_attachment_name_is_empty'] = groom.get_editor_property('attachment_name') == ''
    chain, child, head = [], groom, None
    while child.get_attach_parent():
        parent = child.get_attach_parent()
        socket = str(child.get_attach_socket_name())
        chain.append({'child': child.get_name(), 'parent': parent.get_name(), 'socket': socket})
        if parent.get_name() == 'SKC_HeadFace' and socket == 'headb':
            head = parent
        child = parent
    checks['attached_to_headb_on_head_face'] = head is not None
    details['attachment_chain'] = chain
    for component in spawned.get_components_by_class(unreal.SkeletalMeshComponent):
        mesh = component.get_editor_property('skeletal_mesh_asset')
        if mesh and any('/CapturedMeshes/' + chunk + '/' in mesh.get_path_name() for chunk in ('hair', 'accessories')):
            checks[component.get_name() + '_hidden_on_new_spawn'] = not component.is_visible() and component.get_editor_property('hidden_in_game')
    before = points(groom)
    location = unreal.Vector(123.0, -47.0, 18.0)
    spawned.set_actor_location(location, False, False)
    moved = points(groom)
    expected = [[p[0] + location.x, p[1] + location.y, p[2] + location.z] for p in before]
    checks['character_translation_follows'] = maximum_error(moved, expected) < .002
    yaw = 37.0
    spawned.set_actor_rotation(unreal.Rotator(pitch=0, yaw=yaw, roll=0), False)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    expected = [[p[0] * c - p[1] * s + location.x,
                 p[0] * s + p[1] * c + location.y, p[2] + location.z] for p in before]
    checks['character_rotation_follows'] = maximum_error(points(groom), expected) < .002
    if head:
        initial = head.get_editor_property('relative_location')
        before_head_move = points(groom)
        head.set_relative_location(initial + unreal.Vector(5, 0, 0), False, False)
        after_head_move = points(groom)
        checks['head_component_motion_propagates'] = math.sqrt(sum((a - b) ** 2 for a, b in zip(after_head_move[0], before_head_move[0]))) > 4.9
        head.set_relative_location(initial, False, False)
    details['new_instance_component'] = groom.get_path_name()
    actors.destroy_actor(spawned)
    spawned = None
    details['maps'] = []
    for name in MAPS:
        assert levels.load_level('/Game/TLOU2/Maps/' + name), name
        loaded = list(actors.get_all_level_actors())
        standalone = [a.get_path_name() for a in loaded if isinstance(a, unreal.GroomActor)]
        components = [c for a in loaded for c in a.get_components_by_class(unreal.GroomComponent)]
        checks[name + '_no_standalone_groom_actor'] = len(standalone) == 0
        checks[name + '_one_blueprint_groom'] = len(components) == 1 and components[0].get_owner().get_class() == cls
        details['maps'].append({'map': name, 'standalone_grooms': standalone,
                               'groom_components': [c.get_path_name() for c in components]})
    assert all(checks.values()), checks
finally:
    if spawned:
        actors.destroy_actor(spawned)
    report = {'pass': bool(checks) and all(checks.values()), 'checks': checks,
              'details': details, 'blueprint': BP,
              'method': 'Fresh UE process; new actor from saved BP class; component inheritance, socket ancestry, translation/rotation propagation and all four existing saved maps'}
    (OUT / 'saved_blueprint_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('BLUEPRINT_GROOM_VALIDATION ' + json.dumps(report))
