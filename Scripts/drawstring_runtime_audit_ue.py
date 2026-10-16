"""Inspect the actual game BP and expose matching skin output to the native audit."""
import json
import time
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Drawstring'
started = time.monotonic()
handle = None

def ref(o):
    return o.get_path_name() if o else None

def vec(v):
    return [float(v.x), float(v.y), float(v.z)]

def inspect_runtime(dt):
    if time.monotonic() - started < 2.:
        return
    worlds = [unreal.find_object(None, '/Game/TLOU2/Maps/' + n + '.' + n) for n in ('ElliePatrolCaptureGroomFront', 'ElliePatrolCaptureGroom')]
    world = next((w for w in worlds if w is not None), None)
    if world is None:
        return
    unreal.unregister_slate_post_tick_callback(handle)
    rows = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() != 'SKC_Drawstrings':
                continue
            center, extent, radius = unreal.SystemLibrary.get_component_bounds(c)
            morph_names = [m.get_name() for m in c.get_editor_property('skeletal_mesh_asset').get_editor_property('morph_targets') if 'CaptureAffineCorrective' in m.get_name()]
            animation_curves = {n: c.get_anim_instance().get_curve_value(n) for n in morph_names}
            rows.append({'owner': actor.get_path_name(), 'class': actor.get_class().get_path_name(),
                         'component': c.get_path_name(), 'mesh': ref(c.get_editor_property('skeletal_mesh_asset')),
                         'visible': c.is_visible(), 'hidden_in_game': c.get_editor_property('hidden_in_game'),
                         'animation_mode': str(c.get_editor_property('animation_mode')),
                         'animation': ref(c.get_editor_property('animation_data').get_editor_property('anim_to_play')),
                         'material': ref(c.get_material(0)), 'morph_animation_curves': animation_curves,
                         'world_transform': str(c.get_world_transform()), 'bounds_center_cm': vec(center),
                         'bounds_extent_cm': vec(extent)})
    checks = {'one_blueprint_drawstring_component': len(rows) == 1 and rows[0]['class'].endswith('/BP_ElliePatrolCharacter.BP_ElliePatrolCharacter_C'),
              'visible_after_beginplay': len(rows) == 1 and rows[0]['visible'] and not rows[0]['hidden_in_game'],
              'capture_corrective_active': len(rows) == 1 and bool(rows[0]['morph_animation_curves']) and all(abs(v-1.) < .0001 for v in rows[0]['morph_animation_curves'].values()),
              'chest_bounds': len(rows) == 1 and 120 < rows[0]['bounds_center_cm'][2] < 145 and 2 < rows[0]['bounds_extent_cm'][2] < 15}
    # A temporary upper-body camera gives a clear verification image.
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    cameras = pawn.get_components_by_class(unreal.CameraComponent)
    if cameras:
        location, target = unreal.Vector(0, 105, 143), unreal.Vector(1.5, 0, 137)
        cameras[0].set_field_of_view(35.)
        cameras[0].set_world_location_and_rotation(location, unreal.MathLibrary.find_look_at_rotation(location, target), False, False)
    if hasattr(pawn, 'toggle_catalog_menu'):
        pawn.toggle_catalog_menu()
    report = {'pass': all(checks.values()), 'checks': checks, 'components': rows,
              'method': 'Actual saved game world after Blueprint BeginPlay; native CPU skin output is audited independently in the isolated DrawstringVertexAudit map'}
    (OUT / 'ue_runtime_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('DRAWSTRING_RUNTIME_AUDIT ' + json.dumps(report))

handle = unreal.register_slate_post_tick_callback(inspect_runtime)
