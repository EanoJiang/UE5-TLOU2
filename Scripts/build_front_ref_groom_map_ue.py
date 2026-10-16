import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
SOURCE = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'
DEST = '/Game/TLOU2/Maps/ElliePatrolCaptureGroomFrontRef'
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    levels.load_level(DEST)
else:
    assert levels.new_level_from_template(DEST, SOURCE)
cams = [a for a in actors.get_all_level_actors()
        if isinstance(a, unreal.CameraActor) and 'CatalogCamera' in [str(t) for t in a.tags]]
assert len(cams) == 1
cam = cams[0]
locv = (-65.0, 165.0, 178.0)
tgt = (-5.0, 5.0, 154.0)
loc = unreal.Vector(*locv)
cam.set_actor_location(loc, False, False)
cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, unreal.Vector(*tgt)), False)
cam.camera_component.set_editor_property('field_of_view', 32.0)
assert levels.save_current_level()
(ROOT / 'Exports/Groom/front_ref_map.json').write_text(json.dumps({
    'map': DEST, 'camera_cm': locv, 'target_cm': tgt,
    'horizontal_fov_degrees': 32.0,
}, indent=2))
unreal.log('GROOM_FRONT_REF_MAP ' + json.dumps({'map': DEST, 'camera_cm': locv, 'target_cm': tgt}))
