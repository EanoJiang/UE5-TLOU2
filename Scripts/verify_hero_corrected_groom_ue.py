"""Fresh serialized validation for the corrected full Groom and its Blueprint attachment."""
import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom'
ASSET_PATH = '/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom_HeroCorrected'
MAP_PATH = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'
asset = unreal.load_asset(ASSET_PATH)
assert isinstance(asset, unreal.GroomAsset), ASSET_PATH
groups = []
for row in asset.get_editor_property('hair_groups_info'):
    groups.append({k: row.get_editor_property(k) for k in ('group_id', 'num_curves', 'num_curve_vertices')})
assert {r['group_id']: r['num_curves'] for r in groups} == {0: 34697, 1: 15619, 2: 972, 3: 1666}, groups
assert sum(r['num_curves'] for r in groups) == 52954
for group in asset.get_editor_property('hair_groups_lod'):
    for lod in group.get_editor_property('lods'):
        assert lod.get_editor_property('geometry_type') == unreal.GroomGeometryType.STRANDS
        assert lod.get_editor_property('binding_type') == unreal.GroomBindingType.RIGID
        assert lod.get_editor_property('simulation') == unreal.GroomOverrideType.DISABLE
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level(MAP_PATH)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
grooms = []
hair_sources = []
for actor in actors:
    for c in actor.get_components_by_class(unreal.GroomComponent):
        if c.get_editor_property('groom_asset') == asset:
            child, headb = c, False
            while child.get_attach_parent():
                parent = child.get_attach_parent()
                headb = headb or (parent.get_name() == 'SKC_HeadFace' and str(child.get_attach_socket_name()) == 'headb')
                child = parent
            assert headb
            assert c.get_editor_property('binding_asset') is None
            assert not c.get_editor_property('use_cards')
            grooms.append({'actor': actor.get_path_name(), 'component': c.get_path_name(), 'asset': asset.get_path_name()})
    for c in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        mesh = c.get_editor_property('skeletal_mesh')
        if mesh and '/CaptureMatched1152/CapturedMeshes/' in mesh.get_path_name():
            kind = mesh.get_path_name().split('/CapturedMeshes/')[1].split('/')[0]
            if kind in ('hair', 'accessories'):
                assert c.get_editor_property('hidden_in_game') and not c.get_editor_property('visible'), (kind, c.get_name())
                hair_sources.append(c.get_name())
assert len(grooms) == 1, grooms
assert set(hair_sources) >= {'SKC_Hair', 'SKC_Accessories'}
report = {'pass': True, 'asset': ASSET_PATH, 'map': MAP_PATH, 'groups': groups,
          'groom_components': grooms, 'hidden_source_components': sorted(hair_sources),
          'method': 'Fresh UnrealEditor-Cmd serialized validation'}
(OUT / 'hero_corrected_groom_saved_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('HERO_CORRECTED_GROOM_VALIDATION ' + json.dumps(report))
