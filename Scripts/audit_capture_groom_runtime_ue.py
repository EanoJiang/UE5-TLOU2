"""Inspect the real game world after startup, including BP component visibility."""
import json
import re
import time
from pathlib import Path
import unreal

started = time.monotonic()
handle = None
map_path = re.search(r'(/Game/TLOU2/Maps/ElliePatrolCaptureGroom\w*)', unreal.SystemLibrary.get_command_line()).group(1)
world_path = map_path + '.' + map_path.rsplit('/', 1)[-1]

def inspect_runtime(delta_seconds):
    global handle
    if time.monotonic() - started < 3.0:
        return
    # Standalone -game has no GEditor; editor world helpers dereference it.
    world = unreal.find_object(None, world_path)
    if world is None:
        return
    unreal.unregister_slate_post_tick_callback(handle)
    rows, source_cards, standalone = [], [], []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if isinstance(actor, unreal.GroomActor):
            standalone.append(actor.get_path_name())
        for component in actor.get_components_by_class(unreal.GroomComponent):
            asset = component.get_editor_property('groom_asset')
            center, extent, radius = unreal.SystemLibrary.get_component_bounds(component)
            world_transform = component.get_world_transform()
            chain, child = [], component
            while child.get_attach_parent():
                parent = child.get_attach_parent()
                chain.append({'child': child.get_name(), 'parent': parent.get_name(),
                              'socket': str(child.get_attach_socket_name())})
                child = parent
            rows.append({'actor': actor.get_name(), 'groom': asset.get_path_name(),
                         'component': component.get_path_name(),
                         'owner_class': actor.get_class().get_path_name(),
                         'internal_attachment_name': component.get_editor_property('attachment_name'),
                         'world_translation_cm': [world_transform.translation.x, world_transform.translation.y, world_transform.translation.z],
                         'world_scale': [world_transform.scale3d.x, world_transform.scale3d.y, world_transform.scale3d.z],
                         'relative_location_cm': [component.get_editor_property('relative_location').x, component.get_editor_property('relative_location').y, component.get_editor_property('relative_location').z],
                         'relative_scale': [component.get_editor_property('relative_scale3d').x, component.get_editor_property('relative_scale3d').y, component.get_editor_property('relative_scale3d').z],
                         'attachment_chain': chain,
                         'use_cards': component.get_editor_property('use_cards'),
                         'visible': component.is_visible(),
                         'bounds_center_cm': [center.x, center.y, center.z],
                         'bounds_extent_cm': [extent.x, extent.y, extent.z]})
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_editor_property('skeletal_mesh_asset')
            if mesh and any('/CapturedMeshes/' + name + '/' in mesh.get_path_name() for name in ('hair', 'accessories')):
                source_cards.append({'component': component.get_path_name(),
                                     'mesh': mesh.get_path_name(), 'visible': component.is_visible(),
                                     'hidden_in_game': component.get_editor_property('hidden_in_game')})
    checks = {
        'one_blueprint_groom_component': len(rows) == 1 and rows[0]['owner_class'] == '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter.BP_ElliePatrolCharacter_C',
        'no_standalone_groom_actor': not standalone,
        'no_second_internal_socket_attachment': len(rows) == 1 and rows[0]['internal_attachment_name'] == '',
        'attached_to_head_socket': len(rows) == 1 and any(link['parent'] == 'SKC_HeadFace' and link['socket'] == 'headb' for link in rows[0]['attachment_chain']),
        'strands_active': len(rows) == 1 and rows[0]['visible'] and not rows[0]['use_cards'],
        'verified_groom_asset_active': len(rows) == 1 and rows[0]['groom'] == '/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom.Ellie_Patrol_CaptureGroom',
        'head_bounds': len(rows) == 1 and 130 < rows[0]['bounds_center_cm'][2] < 180 and 3 < rows[0]['bounds_extent_cm'][2] < 40,
        'source_cards_hidden_after_blueprint_startup': len(source_cards) == 2 and all(not row['visible'] and row['hidden_in_game'] for row in source_cards),
    }
    report = {'pass': all(checks.values()), 'checks': checks, 'world': world.get_name(),
              'groom_components': rows, 'standalone_groom_actors': standalone,
              'source_hair_components': source_cards,
              'method': 'Real game-world Python inspection after Blueprint startup and RHI frames',
              'curve_count_evidence': 'Editor-only curve statistics verified separately in saved_asset_validation.json; unavailable in standalone -game Python reflection'}
    Path('D:/TLOU2_UE5_8_Codex/Exports/Groom/runtime_audit_' + world.get_name() + '.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('GROOM_RUNTIME_AUDIT ' + json.dumps(report))

handle = unreal.register_slate_post_tick_callback(inspect_runtime)
