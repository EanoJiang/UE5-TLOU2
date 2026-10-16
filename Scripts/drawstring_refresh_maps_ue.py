"""Refresh serialized character instances, preserving their existing overrides."""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Drawstring'
BP = '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter'
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def ref(o):
    return o.get_path_name() if o else None

def trans(t):
    return {'translation': [t.translation.x, t.translation.y, t.translation.z],
            'rotation': [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w],
            'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z]}

def snapshot(actor):
    rows = {}
    for c in actor.get_components_by_class(unreal.SceneComponent):
        if c.get_name() in ('SKC_Drawstrings', 'SC_DrawstringChestAnchor'):
            continue
        if c.get_class().get_name() in ('BillboardComponent', 'NiagaraComponent'):
            continue
        row = {'relative_transform': trans(c.get_relative_transform()), 'visible': c.is_visible(),
               'hidden': c.get_editor_property('hidden_in_game')}
        if isinstance(c, unreal.SkeletalMeshComponent):
            row.update(mesh=ref(c.get_editor_property('skeletal_mesh_asset')), anim_class=ref(c.get_editor_property('anim_class')),
                       animation=ref(c.get_editor_property('animation_data').get_editor_property('anim_to_play')))
        if isinstance(c, unreal.GroomComponent):
            row.update(groom=ref(c.get_editor_property('groom_asset')), binding=ref(c.get_editor_property('binding_asset')))
        rows[c.get_name()] = row
    return rows

report = {'pass': False, 'maps': []}
try:
    backup = OUT / ('MapBackups_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    bp = unreal.load_asset(BP)
    paths = [p.split('.')[0] for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Maps', recursive=False, include_folder=False) if 'ElliePatrolCaptureGroom' in p]
    for path in paths:
        disk = ROOT / 'Content' / (path.removeprefix('/Game/') + '.umap')
        dst = backup / disk.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(disk, dst)
        before_sha = hashlib.sha256(disk.read_bytes()).hexdigest()
        assert levels.load_level(path)
        characters = [a for a in actors.get_all_level_actors() if a.get_class() == bp.generated_class()]
        assert len(characters) == 1
        label, transform = characters[0].get_actor_label(), trans(characters[0].get_actor_transform())
        before = snapshot(characters[0])
        BlueprintTools.compile_blueprint(bp, warnings_as_errors=True)
        characters = [a for a in actors.get_all_level_actors() if a.get_class() == bp.generated_class()]
        assert len(characters) == 1
        actor = characters[0]
        after = snapshot(actor)
        assert before == after, {'map': path, 'before': before, 'after': after}
        assert actor.get_actor_label() == label and trans(actor.get_actor_transform()) == transform
        strings = [c for c in actor.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'SKC_Drawstrings']
        assert len(strings) == 1 and strings[0].get_editor_property('skeletal_mesh_asset')
        assert hashlib.sha256(disk.read_bytes()).hexdigest() == before_sha, 'Another writer changed this map'
        assert levels.save_current_level()
        report['maps'].append({'map': path, 'character': actor.get_path_name(), 'backup': str(dst),
                               'sha256_before': before_sha, 'sha256_after': hashlib.sha256(disk.read_bytes()).hexdigest(),
                               'original_component_defaults_preserved': before == after, 'saved': True})
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
    # Separate diagnostic map owns a hidden native SkeletalMeshActor so the
    # project's existing C++ CPU-skinned-vertex dump can audit this asset.
    diag = '/Game/TLOU2/Drawstring/Diagnostics/DrawstringVertexAudit'
    assert unreal.EditorLevelLibrary.new_level(diag)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode', unreal.load_class(None, '/Script/TLOU2Codex.CatalogGameMode'))
    proxy = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
    proxy.set_actor_label('Drawstring_CPUSkin_Audit')
    c = proxy.skeletal_mesh_component
    mesh = unreal.load_asset('/Game/TLOU2/Drawstring/SK_Ellie_Patrol_Drawstrings')
    anim = unreal.load_asset('/Game/TLOU2/Drawstring/SK_Ellie_Patrol_Drawstrings_Anim')
    c.set_editor_property('skeletal_mesh_asset', mesh)
    c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    data = c.get_editor_property('animation_data')
    for key, value in {'anim_to_play': anim, 'saved_playing': True, 'saved_looping': True, 'saved_position': 0., 'saved_play_rate': 1.}.items():
        data.set_editor_property(key, value)
    c.set_editor_property('animation_data', data)
    c.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    assert levels.save_current_level()
    report['diagnostic_map'] = diag
    report['pass'] = True
except Exception:
    report['error'] = traceback.format_exc()
    raise
finally:
    (OUT / 'ue_maps_refresh.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('DRAWSTRING_MAP_REFRESH ' + json.dumps(report))
