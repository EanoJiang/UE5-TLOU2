import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Groom'
ASSET_PATH = '/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom_HeroCorrected'
MAPS = ['/Game/TLOU2/Maps/' + n for n in ('ElliePatrolCaptureGroom', 'ElliePatrolCaptureGroomFront', 'ElliePatrolCaptureGroomThreeQuarter', 'ElliePatrolCaptureGroomBack')]
asset = unreal.load_asset(ASSET_PATH)
assert isinstance(asset, unreal.GroomAsset)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for mp in MAPS:
    assert levels.load_level(mp)
    actors = actors_sub.get_all_level_actors()
    matches = []
    for actor in actors:
        for c in actor.get_components_by_class(unreal.GroomComponent):
            if c.get_editor_property('groom_asset') == asset:
                child, headb = c, False
                while child.get_attach_parent():
                    parent = child.get_attach_parent()
                    headb = headb or (parent.get_name() == 'SKC_HeadFace' and str(child.get_attach_socket_name()) == 'headb')
                    child = parent
                assert headb and c.get_editor_property('binding_asset') is None and not c.get_editor_property('use_cards')
                matches.append(c.get_path_name())
        for c in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = c.get_editor_property('skeletal_mesh')
            if mesh and '/CaptureMatched1152/CapturedMeshes/' in mesh.get_path_name():
                kind = mesh.get_path_name().split('/CapturedMeshes/')[1].split('/')[0]
                if kind in ('hair', 'accessories'):
                    assert c.get_editor_property('hidden_in_game') and not c.get_editor_property('visible')
    assert len(matches) == 1, (mp, matches)
    rows.append({'map': mp, 'groom_component': matches[0]})
report = {'pass': True, 'asset': ASSET_PATH, 'maps': rows, 'method': 'Fresh serialized validation across four saved preview maps'}
(OUT / 'hero_corrected_groom_all_maps_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('HERO_CORRECTED_GROOM_ALL_MAPS_VALIDATION ' + json.dumps(report))
