"""Import reconstructed strands and refresh the character Blueprint's Groom.

Run with UnrealEditor-Cmd, -run=pythonscript and the HairStrands and
AlembicHairImporter plugins enabled. The ABC is already in actor-local UE cm;
no axis conversion, skeletal binding, simulation, or recovered-source claim is
applied here. Groom ownership is provided by BP_ElliePatrolCharacter's SCS;
this importer never creates a separate GroomActor.
"""
import hashlib
import json
import traceback
from pathlib import Path

import unreal


ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUTPUT = ROOT / 'Exports/Groom'
GROUPED_ABC = OUTPUT / 'Ellie_Patrol_CaptureGroom_HeroCorrected_Grouped.abc'
ABC = GROUPED_ABC
EXPECTED_CURVES = 52954
EXPECTED_POINTS = 1270896
EXPECTED_GROUP_COUNTS = {0: 34697, 1: 15619, 2: 972, 3: 1666}
REPORT = OUTPUT / 'ue_groom_hero_corrected_import_result.json'
SOURCE_MAP = '/Game/TLOU2/Maps/ElliePatrolCaptureMatched'
TARGET_MAP = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'
DESTINATION = '/Game/TLOU2/Groom'
ASSET_NAME = 'Ellie_Patrol_CaptureGroom_HeroCorrected'
MATERIAL_NAME = 'M_Ellie_CaptureGroom_Hair'
ACTOR_LABEL = 'Ellie_CaptureGroom_StaticStrands'
SOURCE_MAP_FILE = ROOT / 'Content/TLOU2/Maps/ElliePatrolCaptureMatched.umap'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def vector(value):
    return [float(value.x), float(value.y), float(value.z)]


def group_info(asset):
    fields = ['group_index', 'group_id', 'group_name', 'num_curves',
              'num_guides', 'num_curve_vertices', 'num_guide_vertices',
              'max_curve_length']
    rows = []
    for info in asset.get_editor_property('hair_groups_info'):
        row = {key: info.get_editor_property(key) for key in fields}
        row['group_name'] = str(row['group_name'])
        rows.append(row)
    return rows


def build_material():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = DESTINATION + '/' + MATERIAL_NAME
    material = unreal.load_asset(path)
    if material is None:
        material = asset_tools.create_asset(
            MATERIAL_NAME, DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    assert isinstance(material, unreal.Material), path
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_HAIR)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('two_sided', False)
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_HAIR_STRANDS)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -360, -120)
    color.set_editor_property('constant', unreal.LinearColor(0.025, 0.012, 0.006, 1.0))
    color.set_editor_property('desc', 'Reconstructed dark brown strand pigment; not original shader recovery')
    unreal.MaterialEditingLibrary.connect_material_property(
        color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    for prop, value, y in [
        (unreal.MaterialProperty.MP_ROUGHNESS, 0.62, 40),
        (unreal.MaterialProperty.MP_SPECULAR, 0.25, 160),
    ]:
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -360, y)
        node.set_editor_property('r', value)
        unreal.MaterialEditingLibrary.connect_material_property(node, '', prop)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.set_metadata_tag(material, 'ReconstructionScope',
        'UE Hair shading approximation for static capture-derived Groom')
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def import_groom():
    assert ABC.is_file() and ABC.stat().st_size > 1024, str(ABC)
    existing = unreal.load_asset(DESTINATION + '/' + ASSET_NAME)
    if isinstance(existing, unreal.GroomAsset) and unreal.EditorAssetLibrary.get_metadata_tag(
            existing, 'SourceABC_SHA256') == sha256(ABC):
        return existing, [existing.get_path_name()]
    options = unreal.GroomImportOptions()
    conversion = unreal.GroomConversionSettings()
    conversion.set_editor_property('rotation', unreal.Vector(0.0, 0.0, 0.0))
    conversion.set_editor_property('scale', unreal.Vector(1.0, 1.0, 1.0))
    options.set_editor_property('conversion_settings', conversion)
    # This static Groom does not need high-cost shape-matching interpolation.
    # Four source groups are authored with IDs 0..3; no generated animation.
    groups = []
    for _ in range(4):
        group = unreal.HairGroupsInterpolation()
        settings = group.get_editor_property('interpolation_settings')
        settings.set_editor_property('guide_type', unreal.GroomGuideType.GENERATED)
        settings.set_editor_property('interpolation_quality', unreal.HairInterpolationQuality.LOW)
        settings.set_editor_property('interpolation_distance', unreal.HairInterpolationWeight.ROOT)
        settings.set_editor_property('hair_to_guide_density', 0.02)
        settings.set_editor_property('use_unique_guide', True)
        group.set_editor_property('interpolation_settings', settings)
        groups.append(group)
    # The property itself is read-only; mutate its reflected array in place.
    import_groups = options.get_editor_property('interpolation_settings')
    import_groups.extend(groups)
    assert len(options.get_editor_property('interpolation_settings')) == 4
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', str(ABC))
    task.set_editor_property('destination_path', DESTINATION)
    task.set_editor_property('destination_name', ASSET_NAME)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    task.set_editor_property('factory', unreal.HairStrandsFactory())
    task.set_editor_property('options', options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset = unreal.load_asset(DESTINATION + '/' + ASSET_NAME)
    assert isinstance(asset, unreal.GroomAsset), task.get_editor_property('imported_object_paths')
    return asset, list(task.get_editor_property('imported_object_paths'))


def configure_groom(asset, material):
    rendering = list(asset.get_editor_property('hair_groups_rendering'))
    # Imported ABC groups have the default NAME_None material slot; the
    # native MaterialSlotName member is not exposed by UE5.8 Python.
    material_slot = unreal.HairGroupsMaterial()
    material_slot.set_editor_property('material', material)
    material_slot.set_editor_property('slot_name', 'None')
    asset.set_editor_property('hair_groups_materials', [material_slot])
    for group in rendering:
        geometry = group.get_editor_property('geometry_settings')
        # ABC point radii preserve the authored taper. Keep imported width.
        geometry.set_editor_property('hair_width_override', False)
        geometry.set_editor_property('hair_root_scale', 1.0)
        geometry.set_editor_property('hair_tip_scale', 1.0)
        group.set_editor_property('geometry_settings', geometry)
    asset.set_editor_property('hair_groups_rendering', rendering)
    lod_groups = list(asset.get_editor_property('hair_groups_lod'))
    for group in lod_groups:
        lod = unreal.HairLODSettings()
        lod.set_editor_property('geometry_type', unreal.GroomGeometryType.STRANDS)
        lod.set_editor_property('binding_type', unreal.GroomBindingType.RIGID)
        lod.set_editor_property('simulation', unreal.GroomOverrideType.DISABLE)
        lod.set_editor_property('global_interpolation', unreal.GroomOverrideType.DISABLE)
        lod.set_editor_property('curve_decimation', 1.0)
        lod.set_editor_property('vertex_decimation', 1.0)
        group.set_editor_property('lods', [lod])
    asset.set_editor_property('hair_groups_lod', lod_groups)
    physics = list(asset.get_editor_property('hair_groups_physics'))
    for group in physics:
        solver = group.get_editor_property('solver_settings')
        solver.set_editor_property('enable_simulation', False)
        solver.set_editor_property('enable_deformation', False)
        group.set_editor_property('solver_settings', solver)
    asset.set_editor_property('hair_groups_physics', physics)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, 'ReconstructionScope',
        'Reconstructed fibers from captured hair-card geometry, static captured pose; no original strand or simulation recovery')
    unreal.EditorAssetLibrary.set_metadata_tag(asset, 'SourceABC_SHA256', sha256(ABC))
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)


def build_map(asset, material):
    if not unreal.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
        assert unreal.EditorAssetLibrary.does_asset_exist(SOURCE_MAP), 'No existing catalog map is available'
        assert unreal.EditorLevelLibrary.load_level(SOURCE_MAP), SOURCE_MAP
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        assert unreal.EditorLoadingAndSavingUtils.save_map(world, TARGET_MAP), TARGET_MAP
    assert unreal.EditorLevelLibrary.load_level(TARGET_MAP), TARGET_MAP
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    hidden = []
    reference = None
    for actor in list(actors.get_all_level_actors()):
        label = actor.get_actor_label()
        if isinstance(actor, unreal.GroomActor):
            old = actor.get_component_by_class(unreal.GroomComponent)
            if old and old.get_editor_property('groom_asset') == asset:
                assert actors.destroy_actor(actor)
                continue
        for skin in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = skin.get_editor_property('skeletal_mesh')
            if mesh is None:
                continue
            path = mesh.get_path_name()
            is_hair = '/CaptureMatched1152/CapturedMeshes/hair/' in path
            is_accessories = '/CaptureMatched1152/CapturedMeshes/accessories/' in path
            if not (is_hair or is_accessories):
                continue
            if is_hair:
                reference = actor
                location = skin.get_editor_property('relative_location')
                rotation = skin.get_editor_property('relative_rotation')
                scale = skin.get_editor_property('relative_scale3d')
                assert location.is_nearly_zero(0.001), location
                assert max(abs(rotation.pitch), abs(rotation.yaw), abs(rotation.roll)) < 0.001, rotation
                assert max(abs(scale.x - 1), abs(scale.y - 1), abs(scale.z - 1)) < 0.001, scale
            # The current canonical character is a single BP with five mesh
            # components. Hide only the two hair components, not its actor.
            skin.set_visibility(False, True)
            skin.set_hidden_in_game(True, True)
            hidden.append({'label': label, 'actor': actor.get_path_name(),
                           'component': skin.get_path_name(), 'source_mesh': path})
    assert reference is not None and len(hidden) == 2, hidden
    actor = reference
    component = actor.get_component_by_class(unreal.GroomComponent)
    assert component is not None, 'Run integrate_capture_groom_blueprint_ue.py to add the Blueprint SCS Groom component first'
    assert actor.get_class().get_path_name() == '/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter.BP_ElliePatrolCharacter_C'
    child, head_socket = component, False
    while child.get_attach_parent():
        parent = child.get_attach_parent()
        head_socket = head_socket or (parent.get_name() == 'SKC_HeadFace' and str(child.get_attach_socket_name()) == 'headb')
        child = parent
    assert head_socket, 'Blueprint Groom must follow the headb socket'
    component.set_groom_asset(None)
    component.set_groom_asset(asset)
    component.set_enable_simulation(False)
    component.set_editor_property('use_cards', False)
    component.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
    for index in range(max(1, component.get_num_materials())):
        component.set_material(index, material)
    center, extent, sphere_radius = unreal.SystemLibrary.get_component_bounds(component)
    bounds = {'center_cm': vector(center), 'extent_cm': vector(extent),
              'min_cm': vector(center - extent), 'max_cm': vector(center + extent)}
    # The raw ABC is pre-swizzled into UE cm. A second Y-up conversion would
    # put the 1.5m head height on Y instead of Z, so this catches it explicitly.
    null_rhi = '-nullrhi' in unreal.SystemLibrary.get_command_line().lower()
    if null_rhi and max(extent.x, extent.y, extent.z) == 0:
        bounds_state = 'Deferred: NullRHI does not initialize Groom render-resource bounds; validate in real RHI preview.'
        bounds_verified = False
    else:
        assert 130.0 < center.z < 180.0 and 3.0 < extent.z < 40.0, bounds
        assert abs(center.x) < 30.0 and abs(center.y) < 35.0, bounds
        assert 3.0 < extent.x < 40.0 and 3.0 < extent.y < 40.0, bounds
        bounds_state = 'Head-height and extents verified in Unreal world coordinates.'
        bounds_verified = True
    assert unreal.EditorLevelLibrary.save_current_level(), TARGET_MAP
    return {'map': TARGET_MAP, 'groom_actor': actor.get_path_name(),
            'ownership': 'Blueprint SCS default component',
            'standalone_groom_actor': False,
            'attachment_parent': component.get_attach_parent().get_path_name(),
            'attachment_socket': str(component.get_attach_socket_name()),
            'head_bone_socket': 'headb',
            'groom_component': component.get_path_name(),
            'actor_location_cm': vector(actor.get_actor_location()),
            'actor_rotation_degrees': {
                'pitch': actor.get_actor_rotation().pitch,
                'yaw': actor.get_actor_rotation().yaw,
                'roll': actor.get_actor_rotation().roll},
            'bounds': bounds, 'rhi_bounds_verified': bounds_verified,
            'bounds_validation': bounds_state,
            'hidden_source_hair_components': hidden,
            'binding_asset': None, 'simulation_enabled': False}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = sha256(SOURCE_MAP_FILE) if SOURCE_MAP_FILE.is_file() else None
    asset, imported = import_groom()
    material = build_material()
    configure_groom(asset, material)
    info = group_info(asset)
    assert sum(row['num_curves'] for row in info) == EXPECTED_CURVES, info
    # UE5.8 reports 25 built vertices for each 24-point linear ABC strand.
    # Preserve both totals explicitly; raw ABC geometry was validated separately.
    assert all(row['num_curve_vertices'] == row['num_curves'] * 25 for row in info), info
    actual_group_counts = {row['group_id']: row['num_curves'] for row in info}
    grouped = ABC == GROUPED_ABC
    if grouped:
        assert actual_group_counts == EXPECTED_GROUP_COUNTS, info
    report = {'pass': False, 'abc': str(ABC), 'abc_sha256': sha256(ABC),
              'groom_asset': asset.get_path_name(), 'material': material.get_path_name(),
              'imported_object_paths': imported, 'groups': info,
              'curve_count': sum(row['num_curves'] for row in info),
              'point_count': sum(row['num_curve_vertices'] for row in info),
              'source_abc_point_count': EXPECTED_POINTS,
              'source_abc_points_per_curve': 24,
              'ue_built_points_per_curve': 25,
              'point_count_policy': 'UE native built point count is reported independently from the verified ABC point count; no claim of identical native point allocation.',
              'expected_group_curve_counts': EXPECTED_GROUP_COUNTS,
              'actual_group_curve_counts': actual_group_counts,
              'real_group_attributes_imported': grouped and actual_group_counts == EXPECTED_GROUP_COUNTS,
              'conversion': {'rotation_degrees': [0, 0, 0], 'scale': [1, 1, 1],
                             'abc_basis': 'actor-local Unreal X/Y/Z, centimeters'},
              'scope': 'Static capture-derived Groom recreation; strands are reconstructed from hair cards, not recovered original fibers.'}
    report.update(build_map(asset, material))
    after = sha256(SOURCE_MAP_FILE) if SOURCE_MAP_FILE.is_file() else None
    assert before == after, 'Canonical catalog map changed'
    report['canonical_map_sha256_unchanged'] = before
    report['legacy_source_map_present'] = SOURCE_MAP_FILE.is_file()
    report['pass'] = True
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('CAPTURE_GROOM_IMPORT ' + json.dumps(report))


try:
    main()
except Exception:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({'pass': False, 'error': traceback.format_exc()}, indent=2), encoding='utf-8')
    raise

