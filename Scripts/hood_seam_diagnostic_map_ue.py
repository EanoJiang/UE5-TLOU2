"""Create a separate native CPU-skin audit map; run in an isolated commandlet."""
import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/HoodSeam'
DIAGNOSTIC = '/Game/TLOU2/HoodSeam/Diagnostics/BodyVertexAudit'
ASSET = '/Game/TLOU2/CaptureMatched1152/CapturedMeshes/body_clothing/Ellie_Patrol_body_clothing_Pruned'
report = json.loads((OUT / 'ue_import.json').read_text())
assert report['pass']
mesh = unreal.load_asset(ASSET)
assert mesh
assert unreal.EditorLevelLibrary.new_level(DIAGNOSTIC)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', unreal.load_class(None, '/Script/TLOU2Codex.CatalogGameMode'))
actor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
actor.set_actor_label('HoodSeam_BodyVertexAudit')
actor.set_editor_property('tags', ['CaptureAffineCorrective'])
component = actor.skeletal_mesh_component
component.set_editor_property('skeletal_mesh_asset', mesh)
component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
animation = unreal.load_asset('/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim')
data = component.get_editor_property('animation_data')
for key, value in {'anim_to_play': animation, 'saved_playing': True, 'saved_looping': True, 'saved_position': 0., 'saved_play_rate': 1.}.items():
    data.set_editor_property(key, value)
component.set_editor_property('animation_data', data)
component.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(OUT / 'diagnostic_map.json').write_text(json.dumps({'pass': True, 'map': DIAGNOSTIC, 'only_new_diagnostic_map_saved': True}, indent=2))
