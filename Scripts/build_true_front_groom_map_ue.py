"""Create a true frontal close-up map for Groom placement verification."""
import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
SOURCE = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'
DEST = '/Game/TLOU2/Maps/ElliePatrolCaptureGroomTrueFront'
OUT = ROOT / 'Exports/Groom'
OUT.mkdir(parents=True, exist_ok=True)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    levels.load_level(DEST)
else:
    assert levels.new_level_from_template(DEST, SOURCE), DEST

cameras = [a for a in actors.get_all_level_actors()
           if isinstance(a, unreal.CameraActor) and 'CatalogCamera' in [str(t) for t in a.tags]]
assert len(cameras) == 1, [a.get_actor_label() for a in cameras]
camera = cameras[0]
# The character's face is aligned toward +Y with a slight world-X offset.
location = (65.0, 165.0, 178.0)
target = (-5.0, 5.0, 154.0)
loc, aim = unreal.Vector(*location), unreal.Vector(*target)
camera.set_actor_location(loc, False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, aim), False)
camera.camera_component.set_editor_property('field_of_view', 32.0)
assert levels.save_current_level(), DEST
(OUT / 'true_front_map.json').write_text(json.dumps({
    'map': DEST, 'camera_cm': location, 'target_cm': target,
    'horizontal_fov_degrees': 32.0,
}, indent=2), encoding='utf-8')
unreal.log('GROOM_TRUE_FRONT_MAP ' + json.dumps({'map': DEST, 'camera_cm': location, 'target_cm': target}))
