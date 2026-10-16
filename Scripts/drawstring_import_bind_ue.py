"""Import the independently recovered strings and persist a blueprint default.

Run only with the interactive editor closed. Existing mesh/animation/groom
defaults are compared before and after; only the new strings component is added.
"""
import hashlib
import importlib.util
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal
from editor_toolset.toolsets.actor import ActorTools
from editor_toolset.toolsets.blueprint import BlueprintTools

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT / 'Exports/Drawstring'
DEST = '/Game/TLOU2/Drawstring'
BP_PATH = '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter'
NAME, ANCHOR, BODY, BONE = 'SKC_Drawstrings', 'SC_DrawstringChestAnchor', 'SKC_BodyClothing', 'spined'

def ref(o):
    return o.get_path_name() if o else None

def vec(v):
    return [float(v.x), float(v.y), float(v.z)]

def transform(t):
    return {'translation': vec(t.translation), 'scale': vec(t.scale3d),
            'rotation_xyzw': [t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w]}

def templates(bp):
    return {c.get_name().removesuffix('_GEN_VARIABLE'): c for c in ActorTools.get_components(BlueprintTools.get_default_object(bp))}

def snapshot(c):
    row = {'class': c.get_class().get_name(), 'relative_transform': transform(c.get_relative_transform()),
           'visible': c.is_visible(), 'hidden': c.get_editor_property('hidden_in_game')}
    if isinstance(c, unreal.SkeletalMeshComponent):
        data = c.get_editor_property('animation_data')
        row.update(mesh=ref(c.get_editor_property('skeletal_mesh_asset')),
                   anim_class=ref(c.get_editor_property('anim_class')),
                   animation_mode=str(c.get_editor_property('animation_mode')),
                   animation=ref(data.get_editor_property('anim_to_play')),
                   playing=data.get_editor_property('saved_playing'), looping=data.get_editor_property('saved_looping'))
    elif isinstance(c, unreal.GroomComponent):
        sim = c.get_editor_property('simulation_settings')
        row.update(groom=ref(c.get_editor_property('groom_asset')),
                   binding=ref(c.get_editor_property('binding_asset')),
                   simulation_override=sim.get_editor_property('override_settings'),
                   simulation_enabled=sim.get_editor_property('solver_settings').get_editor_property('enable_simulation'))
    return row

def set_transform(c, t):
    c.modify()
    c.set_editor_property('relative_location', t.translation)
    c.set_editor_property('relative_rotation', t.rotation.rotator())
    c.set_editor_property('relative_scale3d', t.scale3d)

def main(report):
    OUT.mkdir(parents=True, exist_ok=True)
    for filename in ('source_verification.json', 'blender_fbx_verification.json', 'captured_fbx_verification.json'):
        gate = json.loads((OUT / filename).read_text())
        assert gate.get('pass'), (filename, gate)
    fbx = OUT / 'SK_Ellie_Patrol_Drawstrings.fbx'
    assert fbx.is_file()
    task = unreal.AssetImportTask()
    task.filename = str(fbx)
    task.destination_path = DEST
    task.automated = True
    task.replace_existing = True
    task.save = True
    ui = unreal.FbxImportUI()
    for prop, value in {'import_mesh': True, 'import_as_skeletal': True,
                        'import_animations': True, 'import_materials': False,
                        'import_textures': False, 'create_physics_asset': False,
                        'automated_import_should_detect_type': False}.items():
        ui.set_editor_property(prop, value)
    ui.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    md = ui.get_editor_property('skeletal_mesh_import_data')
    md.set_editor_property('import_morph_targets', True)
    md.set_editor_property('morph_threshold_position', .000001)
    task.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [unreal.load_asset(p) for p in task.imported_object_paths]
    meshes = [a for a in imported if isinstance(a, unreal.SkeletalMesh)]
    animations = [a for a in imported if isinstance(a, unreal.AnimSequence)]
    # UE's reimport path only reports the existing mesh; the saved animation
    # remains its own asset and must be resolved and checked explicitly.
    if len(meshes) == 1 and not animations:
        existing = unreal.load_asset(DEST + '/SK_Ellie_Patrol_Drawstrings_Anim')
        if isinstance(existing, unreal.AnimSequence):
            assert Path(existing.get_editor_property('asset_import_data').get_first_filename()).resolve() == fbx.resolve()
            animations = [existing]
    assert len(meshes) == 1 and len(animations) == 1, list(task.imported_object_paths)
    mesh, anim = meshes[0], animations[0]
    report['imported'] = list(task.imported_object_paths)
    assert mesh.get_editor_property('skeleton') == anim.get_skeleton()
    editor = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    settings = editor.get_lod_build_settings(mesh, 0)
    for prop, value in {'bone_influence_limit': 8, 'use_high_precision_skin_weights': True,
                        'use_full_precision_u_vs': True, 'use_high_precision_tangent_basis': True,
                        'morph_threshold_position': .000001}.items():
        settings.set_editor_property(prop, value)
    editor.set_lod_build_settings(mesh, 0, settings)
    compression = unreal.load_asset('/Game/TLOU2/CaptureMatched1152/Settings/CaptureBoneFullFloat')
    assert isinstance(compression, unreal.AnimBoneCompressionSettings)
    assert all(c.get_class().get_name() == 'AnimCompress_LeastDestructive' for c in compression.get_editor_property('codecs'))
    anim.set_editor_property('enable_root_motion', False)
    anim.set_editor_property('allow_frame_stripping', False)
    anim.set_editor_property('do_not_override_compression', True)
    unreal.AnimationLibrary.set_bone_compression_settings(anim, compression)
    morphs = [m.get_name() for m in mesh.get_editor_property('morph_targets') if 'CaptureAffineCorrective' in m.get_name()]
    assert morphs, 'The captured pose requires an imported affine corrective'
    skeleton = mesh.get_editor_property('skeleton')
    for name in morphs:
        curve_type = unreal.RawCurveTrackTypes.RCT_FLOAT
        if not unreal.AnimationLibrary.does_curve_exist(anim, name, curve_type):
            unreal.AnimationLibrary.add_curve(anim, name, curve_type, False)
        unreal.AnimationLibrary.add_float_curve_keys(anim, name, [0., float(anim.get_play_length())], [1., 1.])
        unreal.AnimationLibrary.set_curve_meta_data_morph_target(skeleton, name, True)
        assert all(abs(unreal.AnimationLibrary.get_float_value_at_time(anim, name, t)-1.) < 1e-6 for t in (0., anim.get_play_length()/2., anim.get_play_length()))
    report['corrective_morphs'] = morphs
    spec = importlib.util.spec_from_file_location('drawstring_material', ROOT / 'Scripts/drawstring_material_ue.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    material = module.build_material()
    assert isinstance(material, unreal.MaterialInterface)
    slots = list(mesh.get_editor_property('materials'))
    assert len(slots) == 1
    slots[0].set_editor_property('material_interface', material)
    mesh.set_editor_property('materials', slots)
    for asset in (mesh, anim, mesh.get_editor_property('skeleton')):
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset), ref(asset)
    report.update(mesh=ref(mesh), animation=ref(anim), material=ref(material),
                  bone_compression=ref(compression), source_fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest())

    # Back up the authoritative on-disk blueprint before loading/mutating it.
    source_bp = ROOT / 'Content/TLOU2/Blueprints/BP_ElliePatrolCharacter.uasset'
    backup = OUT / ('Backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')) / 'BP_ElliePatrolCharacter.uasset'
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_bp, backup)
    report['backup'] = str(backup)
    report['blueprint_sha256_before'] = hashlib.sha256(source_bp.read_bytes()).hexdigest()
    bp = unreal.load_asset(BP_PATH)
    original = templates(bp)
    report['original_components_before'] = {n: snapshot(c) for n, c in original.items() if n not in (NAME, ANCHOR)}
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    probe = actors.spawn_actor_from_class(bp.generated_class(), unreal.Vector())
    body = next(c for c in probe.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == BODY)
    assert body.get_bone_index(BONE) >= 0
    captured = body.get_socket_transform(BONE, unreal.RelativeTransformSpace.RTS_COMPONENT)
    relative = captured.inverse()
    neutral = unreal.MathLibrary.compose_transforms(relative, captured)
    assert max(abs(v) for v in vec(neutral.translation)) < .001
    assert max(abs(v - 1) for v in vec(neutral.scale3d)) < .00001
    assert actors.destroy_actor(probe)
    if ANCHOR not in original:
        ActorTools.add_component(original[BODY], unreal.SceneComponent.static_class(), ANCHOR)
    current = templates(bp)
    if NAME not in current:
        ActorTools.add_component(current[ANCHOR], unreal.SkeletalMeshComponent.static_class(), NAME)
    current = templates(bp)
    anchor, component = current[ANCHOR], current[NAME]
    assert ActorTools.set_parent_component(anchor, current[BODY])
    assert ActorTools.set_parent_component(component, anchor)
    current = templates(bp)
    anchor, component = current[ANCHOR], current[NAME]
    assert unreal.GroomBlueprintEditorLibrary.set_blueprint_component_socket(bp, anchor, BONE)
    assert unreal.GroomBlueprintEditorLibrary.set_blueprint_component_socket(bp, component, unreal.Name())
    set_transform(anchor, relative)
    set_transform(component, unreal.Transform())
    component.set_editor_property('skeletal_mesh_asset', mesh)
    component.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    component.set_editor_property('anim_class', None)
    data = component.get_editor_property('animation_data')
    for prop, value in {'anim_to_play': anim, 'saved_looping': True, 'saved_playing': True,
                        'saved_position': 0., 'saved_play_rate': 1.}.items():
        data.set_editor_property(prop, value)
    component.set_editor_property('animation_data', data)
    component.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    component.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    component.set_visibility(True, False)
    component.set_hidden_in_game(False, False)
    component.set_material(0, material)
    component.set_editor_property('component_tags', ['OriginalDrawstring22', 'CapturedStaticClothPose'])
    bp.modify()
    BlueprintTools.compile_blueprint(bp, warnings_as_errors=True)
    final = templates(bp)
    assert final[NAME].get_editor_property('skeletal_mesh_asset') == mesh, 'New mesh default did not survive blueprint compilation'
    report['original_components_after'] = {n: snapshot(final[n]) for n in report['original_components_before']}
    assert report['original_components_before'] == report['original_components_after'], 'An existing component default changed'
    report['component'] = snapshot(final[NAME])
    report['anchor_relative_transform'] = transform(relative)
    report['captured_chest_transform'] = transform(captured)
    report['scs_component'] = json.loads(unreal.GroomBlueprintEditorLibrary.describe_blueprint_component_attachment(bp, final[NAME]))
    report['scs_anchor'] = json.loads(unreal.GroomBlueprintEditorLibrary.describe_blueprint_component_attachment(bp, final[ANCHOR]))
    assert report['scs_component']['parent_component'] == ANCHOR + '_GEN_VARIABLE'
    assert report['scs_anchor']['parent_component'] == BODY + '_GEN_VARIABLE'
    assert report['scs_anchor']['attach_to_name'] == BONE
    assert hashlib.sha256(source_bp.read_bytes()).hexdigest() == report['blueprint_sha256_before'], 'Blueprint was changed by another writer during integration'
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
    report['blueprint_sha256_after'] = hashlib.sha256(source_bp.read_bytes()).hexdigest()
    original_pak = Path(json.loads((OUT / 'capture.json').read_text())['source_package'])
    shutil.copy2(original_pak, ROOT / 'Content/TLOU2/SourcePaks' / original_pak.name)
    report['pass'] = True
    report['policy'] = 'Original owned 22-node skin, captured hold pose and corrective; independent component follows chest socket through inverse captured transform. No invented dynamic cloth simulation.'

report = {'pass': False, 'blueprint': BP_PATH, 'component_name': NAME}
try:
    main(report)
except Exception:
    report['error'] = traceback.format_exc()
    raise
finally:
    (OUT / 'ue_import_binding.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('DRAWSTRING_IMPORT_BINDING ' + json.dumps(report))
