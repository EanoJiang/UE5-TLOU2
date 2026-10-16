"""Reload the saved Groom/map in a fresh editor process and check persistence."""
import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom'
imported = json.loads((OUT / 'ue_groom_import_result.json').read_text(encoding='utf-8'))
assert imported['pass'], imported
groom = unreal.load_asset(imported['groom_asset'])
assert isinstance(groom, unreal.GroomAsset), imported['groom_asset']
material = unreal.load_asset(imported['material'])
checks = {}
checks['hair_shading_model'] = material.get_editor_property('shading_model') == unreal.MaterialShadingModel.MSM_HAIR
groups = list(groom.get_editor_property('hair_groups_info'))
curves = sum(g.get_editor_property('num_curves') for g in groups)
points = sum(g.get_editor_property('num_curve_vertices') for g in groups)
checks['curve_count_persisted'] = curves == imported['curve_count'] and curves > 5000
checks['point_count_persisted'] = points == imported['point_count']
for index, group in enumerate(groom.get_editor_property('hair_groups_lod')):
    lods = list(group.get_editor_property('lods'))
    checks['group_%d_strands' % index] = all(lod.get_editor_property('geometry_type') == unreal.GroomGeometryType.STRANDS for lod in lods)
    checks['group_%d_simulation_disabled' % index] = all(lod.get_editor_property('simulation') == unreal.GroomOverrideType.DISABLE for lod in lods)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level(imported['map']), imported['map']
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
groom_components = [c for a in actors for c in a.get_components_by_class(unreal.GroomComponent)]
checks['no_standalone_groom_actor'] = not any(isinstance(a, unreal.GroomActor) for a in actors)
checks['exactly_one_blueprint_groom_component'] = len(groom_components) == 1
if groom_components:
    component = groom_components[0]
    actor = component.get_owner()
    checks['character_blueprint_owns_groom'] = actor.get_class().get_path_name() == '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter.BP_ElliePatrolCharacter_C'
    child, head_socket = component, False
    while child.get_attach_parent():
        parent = child.get_attach_parent()
        head_socket = head_socket or (parent.get_name() == 'SKC_HeadFace' and str(child.get_attach_socket_name()) == 'headb')
        child = parent
    checks['head_socket_assignment_persisted'] = head_socket
    checks['groom_assignment_persisted'] = component.get_editor_property('groom_asset') == groom
    checks['real_strands_enabled'] = not component.get_editor_property('use_cards')
    checks['material_assignment_persisted'] = component.get_material(0) == material
    checks['no_unverified_skin_binding'] = component.get_editor_property('binding_asset') is None
    center, extent, sphere_radius = unreal.SystemLibrary.get_component_bounds(component)
    if extent.length() > 0:
        checks['head_height_bounds_persisted'] = 130 < center.z < 180 and 3 < extent.z < 40
    location = actor.get_actor_location()
    checks['capture_placement_persisted'] = max(abs(x - y) for x, y in zip((location.x, location.y, location.z), imported['actor_location_cm'])) < .001
for chunk in ('hair', 'accessories'):
    matches = []
    for owner in actors:
        for component in owner.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_editor_property('skeletal_mesh_asset')
            if mesh and '/CapturedMeshes/' + chunk + '/' in mesh.get_path_name():
                matches.append(component)
    checks[chunk + '_source_cards_hidden'] = len(matches) == 1 and not matches[0].is_visible()

report = {'pass': all(checks.values()), 'checks': checks,
          'curve_count': curves, 'point_count': points,
          'map': imported['map'], 'groom_asset': groom.get_path_name(),
          'method': 'Fresh UnrealEditor-Cmd reload of serialized Groom and level',
          'spatial_render_validation': 'Use actual RHI previews/live-editor validation; NullRHI does not create Groom render bounds'}
(OUT / 'saved_asset_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
assert report['pass'], report
unreal.log('CAPTURE_GROOM_SAVED_VERIFIED ' + json.dumps(report))
