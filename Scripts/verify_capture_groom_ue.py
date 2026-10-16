"""Independently read saved Groom/map state; does not save any UE asset."""
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom'
applied = json.loads((OUT / 'ue_groom_import_result.json').read_text())
asset = unreal.load_asset(applied['groom_asset'])
assert isinstance(asset, unreal.GroomAsset)
groups = []
for row in asset.get_editor_property('hair_groups_info'):
    groups.append({key: row.get_editor_property(key) for key in (
        'group_id', 'num_curves', 'num_curve_vertices')})
assert {row['group_id']: row['num_curves'] for row in groups} == {
    0: 34697, 1: 15619, 2: 972, 3: 1666}, groups
lod_settings = []
for group in asset.get_editor_property('hair_groups_lod'):
    lods = group.get_editor_property('lods')
    assert len(lods) == 1
    lod = lods[0]
    assert lod.get_editor_property('geometry_type') == unreal.GroomGeometryType.STRANDS
    assert lod.get_editor_property('binding_type') == unreal.GroomBindingType.RIGID
    assert lod.get_editor_property('simulation') == unreal.GroomOverrideType.DISABLE
    assert lod.get_editor_property('global_interpolation') == unreal.GroomOverrideType.DISABLE
    lod_settings.append(lod.export_text())
for group in asset.get_editor_property('hair_groups_physics'):
    solver = group.get_editor_property('solver_settings')
    assert not solver.get_editor_property('enable_simulation')
    assert not solver.get_editor_property('enable_deformation')
slots = asset.get_editor_property('hair_groups_materials')
assert slots and all(slot.get_editor_property('material').get_path_name() == applied['material'] for slot in slots)
material = unreal.load_asset(applied['material'])
assert material.get_editor_property('shading_model') == unreal.MaterialShadingModel.MSM_HAIR
assert unreal.EditorLevelLibrary.load_level(applied['map'])
grooms = []
skin_state = []
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    assert not isinstance(actor, unreal.GroomActor), 'Standalone GroomActor remains: ' + actor.get_path_name()
    component = actor.get_component_by_class(unreal.GroomComponent)
    if component:
        assert actor.get_class().get_path_name() == '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter.BP_ElliePatrolCharacter_C'
        child, head_socket = component, False
        while child.get_attach_parent():
            parent = child.get_attach_parent()
            head_socket = head_socket or (parent.get_name() == 'SKC_HeadFace' and str(child.get_attach_socket_name()) == 'headb')
            child = parent
        assert head_socket
        assert component.get_editor_property('groom_asset') == asset
        assert component.get_editor_property('binding_asset') is None
        assert not component.get_editor_property('use_cards')
        assert all(component.get_material(i) == material for i in range(component.get_num_materials()))
        grooms.append({'actor': actor.get_path_name(), 'component': component.get_path_name()})
    for skin in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        mesh = skin.get_editor_property('skeletal_mesh')
        if mesh is None or '/CaptureMatched1152/CapturedMeshes/' not in mesh.get_path_name():
            continue
        kind = mesh.get_path_name().split('/CapturedMeshes/')[1].split('/')[0]
        hidden = skin.get_editor_property('hidden_in_game')
        visible = skin.get_editor_property('visible')
        expected_hidden = kind in ('hair', 'accessories')
        assert bool(hidden) == expected_hidden and bool(visible) != expected_hidden, (kind, hidden, visible)
        skin_state.append({'kind': kind, 'component': skin.get_path_name(), 'visible': visible,
                           'hidden_in_game': hidden})
assert len(grooms) == 1 and len(skin_state) == 5, (grooms, skin_state)
source_map = ROOT / 'Content/TLOU2/Maps/ElliePatrolCaptureMatched.umap'
canonical_hash = hashlib.sha256(source_map.read_bytes()).hexdigest() if source_map.is_file() else None
if canonical_hash:
    assert canonical_hash == applied['canonical_map_sha256_unchanged']
report = {'pass': True, 'method': 'Fresh Unreal process reads saved asset/map without asset saves.',
          'groups': groups, 'lod_settings': lod_settings, 'groom_components': grooms,
          'skin_component_visibility': skin_state, 'canonical_map_sha256_unchanged': canonical_hash,
          'ownership': 'Character Blueprint SCS Groom component on headb socket',
          'rhi_rendering_validation': 'Separate real RHI preview required; NullRHI persistence check only.'}
(OUT / 'ue_groom_saved_state_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('CAPTURE_GROOM_SAVED_STATE_VALIDATION ' + json.dumps(report))
