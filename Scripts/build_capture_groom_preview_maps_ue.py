"""Create saved, reproducible close-up cameras for actual RHI Groom checks."""
import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
SOURCE = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'
OUT = ROOT / 'Exports/Groom'
OUT.mkdir(parents=True, exist_ok=True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

views = {
    'Front': ((-5.0, 108.0, 158.0), (-5.0, 5.0, 154.0)),
    'ThreeQuarter': ((68.0, 85.0, 162.0), (-5.0, 5.0, 154.0)),
    'Back': ((-5.0, -102.0, 160.0), (-5.0, 5.0, 154.0)),
}
result = []
for name, (location, target) in views.items():
    path = SOURCE + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        assert levels.load_level(path), path
    else:
        assert levels.new_level_from_template(path, SOURCE), path
    cameras = [a for a in actors.get_all_level_actors()
               if isinstance(a, unreal.CameraActor) and 'CatalogCamera' in [str(t) for t in a.tags]]
    assert len(cameras) == 1, [a.get_actor_label() for a in cameras]
    camera = cameras[0]
    loc, aim = unreal.Vector(*location), unreal.Vector(*target)
    camera.set_actor_location(loc, False, False)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, aim), False)
    camera.camera_component.set_editor_property('field_of_view', 32.0)
    assert levels.save_current_level(), path
    result.append({'view': name, 'map': path, 'camera_cm': location,
                   'target_cm': target, 'horizontal_fov_degrees': 32.0})

assert levels.load_level(SOURCE), SOURCE
(OUT / 'preview_maps.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
unreal.log('GROOM_PREVIEW_MAPS ' + json.dumps(result))
