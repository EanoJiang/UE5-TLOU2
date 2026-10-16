"""Apply primary material maps only; prove mesh/rig/action/frame invariance."""
import bpy
import hashlib
import json
import os
from pathlib import Path
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
MANIFEST = json.loads((ROOT / 'Exports/source_character_material_manifest.json').read_text())
SOURCES = [ROOT / 'Blender' / (name + '.blend') for name in [
    'Ellie_Patrol_Catalog_CaptureMatched', 'Ellie_Patrol_CapturedSkinPose',
    'Ellie16_Patrol_OriginalViewerPose', 'Ellie_Patrol_Original_0FW']]


def array_hash(collection, field, width, dtype='float32'):
    a = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(field, a)
    return hashlib.sha256(a.tobytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def signature():
    meshes = {}
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        m = o.data
        weights = [(v.index, [(g.group, g.weight) for g in v.groups]) for v in m.vertices]
        row = {'vertices': len(m.vertices), 'loops': len(m.loops),
               'vertex_co_sha256': array_hash(m.vertices, 'co', 3),
               'loop_vertex_sha256': array_hash(m.loops, 'vertex_index', 1, 'int32'),
               'edges_sha256': array_hash(m.edges, 'vertices', 2, 'int32'),
               'polygon_loops_sha256': array_hash(m.polygons, 'loop_start', 1, 'int32'),
               'polygon_sizes_sha256': array_hash(m.polygons, 'loop_total', 1, 'int32'),
               'polygon_material_sha256': array_hash(m.polygons, 'material_index', 1, 'int32'),
               'polygon_smooth_sha256': array_hash(m.polygons, 'use_smooth', 1, 'bool'),
               'uv_sha256': {uv.name: array_hash(uv.data, 'uv', 2) for uv in m.uv_layers},
               'weight_sha256': digest(weights), 'vertex_groups': [g.name for g in o.vertex_groups],
               'shape_keys': {k.name: array_hash(k.data, 'co', 3) for k in m.shape_keys.key_blocks} if m.shape_keys else {},
               'world_matrix': [list(r) for r in o.matrix_world],
               'modifiers': [(x.name, x.type, getattr(getattr(x, 'object', None), 'name', None)) for x in o.modifiers]}
        meshes[o.name] = row
    rigs = {}
    for o in bpy.data.objects:
        if o.type != 'ARMATURE':
            continue
        rigs[o.name] = {'bones': [(b.name, b.parent.name if b.parent else None,
                                  [list(r) for r in b.matrix_local], b.use_deform) for b in o.data.bones],
                       'pose': [(p.name, list(p.location), list(p.rotation_quaternion), list(p.rotation_euler),
                                 list(p.scale), p.rotation_mode) for p in o.pose.bones],
                       'matrix_world': [list(r) for r in o.matrix_world]}
    actions = {}
    for action in bpy.data.actions:
        curves = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', []):
                    for f in bag.fcurves:
                        curves.append({'path': f.data_path, 'index': f.array_index,
                                       'keys': array_hash(f.keyframe_points, 'co', 2),
                                       'left': array_hash(f.keyframe_points, 'handle_left', 2),
                                       'right': array_hash(f.keyframe_points, 'handle_right', 2),
                                       'interpolation': [k.interpolation for k in f.keyframe_points],
                                       'extrapolation': f.extrapolation})
        actions[action.name] = {'users': action.users, 'curves': curves, 'frame_range': list(action.frame_range),
                                'slots': [(s.identifier, s.target_id_type) for s in action.slots]}
    sc = bpy.context.scene
    return {'meshes': meshes, 'rig_sha256': digest(rigs), 'action_sha256': digest(actions),
            'actions': {n: {'users': a['users'], 'fcurves': len(a['curves'])} for n, a in actions.items()},
            'object_actions': {o.name: o.animation_data.action.name for o in bpy.data.objects if o.animation_data and o.animation_data.action},
            'frame': sc.frame_current, 'subframe': sc.frame_subframe, 'range': [sc.frame_start, sc.frame_end],
            'fps': [sc.render.fps, sc.render.fps_base]}


def image(stem, space):
    path = ROOT / 'Exports/TexturesDecoded' / (stem + '.png')
    assert path.exists(), path
    im = bpy.data.images.load(str(path), check_existing=True)
    im.colorspace_settings.name = space
    return im


def texture(mat, name, stem, space):
    nt = mat.node_tree
    n = nt.nodes.get(name) or nt.nodes.new('ShaderNodeTexImage')
    n.name = name
    n.image = image(stem, space)
    return n


def apply_material(name, spec):
    mat = bpy.data.materials.get('M_ND_' + name)
    assert mat and mat.use_nodes, name
    nt = mat.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    color = texture(mat, 'ND_Color_' + name, spec['color_stem'], 'sRGB')
    nt.links.new(color.outputs['Color'], bs.inputs['Base Color'])
    normal = texture(mat, 'ND_Normal_' + name, spec['normal_stem'], 'Non-Color')
    nm = nt.nodes.get('ND_NormalMap_' + name) or nt.nodes.new('ShaderNodeNormalMap')
    nm.name = 'ND_NormalMap_' + name
    nm.space = 'TANGENT'
    nm.uv_map = ''  # Explicitly use each mesh's active UV layer.
    nm.inputs['Strength'].default_value = spec['portable_normal_node_strength']
    nt.links.new(normal.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
    for link in list(bs.inputs['Roughness'].links):
        nt.links.remove(link)
    if spec['roughness_stem']:
        rough = texture(mat, 'ND_SourcePrimary_Roughness_' + name, spec['roughness_stem'], 'Non-Color')
        nt.links.new(rough.outputs['Color'], bs.inputs['Roughness'])
    else:
        bs.inputs['Roughness'].default_value = spec['roughness_constant']
    ao = texture(mat, 'ND_Ao_' + name, spec['ao_stem'], 'Non-Color')
    # Official glTF exporter recognizes this group socket. Keep AO separate
    # from base color because Principled has no ambient-only AO input.
    group = bpy.data.node_groups.get('glTF Material Output')
    if group is None:
        group = bpy.data.node_groups.new('glTF Material Output', 'ShaderNodeTree')
        group.interface.new_socket(name='Occlusion', in_out='INPUT', socket_type='NodeSocketFloat')
    gn = nt.nodes.get('ND_SourcePrimary_glTF_Occlusion') or nt.nodes.new('ShaderNodeGroup')
    gn.name = 'ND_SourcePrimary_glTF_Occlusion'
    gn.node_tree = group
    nt.links.new(ao.outputs['Color'], gn.inputs['Occlusion'])
    for channel in ['color', 'normal', 'ao']:
        mat['decoded_' + channel + '_texture'] = str(ROOT / 'Exports/TexturesDecoded' / (spec[channel + '_stem'] + '.png'))
    mat['source_primary_material_manifest'] = 'Exports/source_character_material_manifest.json'
    mat['source_normal_xy_strength'] = spec['source_normal_strength']
    mat['portable_normal_strength'] = spec['portable_normal_node_strength']
    mat['material_policy'] = spec['scope']
    mat['source_primary_roughness_equation'] = spec['formulas']['roughness']
    return {'material': mat.name, 'color': color.image.name, 'normal': normal.image.name,
            'ao': ao.image.name, 'normal_node_strength': nm.inputs['Strength'].default_value,
            'normal_space': nm.space, 'normal_uv': 'active UV',
            'roughness': spec['roughness_stem'] or spec['roughness_constant'],
            'ao_export_socket': gn.node_tree.name + '.Occlusion'}


def dependencies(node, seen):
    if node in seen:
        return set()
    seen.add(node)
    out = {node.image} if node.type == 'TEX_IMAGE' and node.image else set()
    for socket in node.inputs:
        for link in socket.links:
            out.update(dependencies(link.from_node, seen))
    return out


results = []
for source in SOURCES:
    bpy.ops.wm.open_mainfile(filepath=str(source))
    before = signature()
    rows = [apply_material(name, spec) for name, spec in MANIFEST['materials'].items()]
    used = set()
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        for mat in o.data.materials:
            if not mat or not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if (node.type == 'OUTPUT_MATERIAL' and node.is_active_output) or (node.type == 'GROUP' and node.node_tree and node.node_tree.name.startswith('glTF Material Output')):
                    used.update(dependencies(node, set()))
    packed = []
    for im in sorted(used, key=lambda x: x.name):
        path = bpy.path.abspath(im.filepath)
        if not im.packed_file:
            assert os.path.isfile(path), path
            im.pack()
        if os.path.isfile(path):
            im.filepath = bpy.path.relpath(path, start=str(source.parent))
        packed.append({'image': im.name, 'source_filepath': path, 'portable_filepath': im.filepath,
                       'packed': bool(im.packed_file), 'dimensions': list(im.size)})
    after = signature()
    assert before == after, ('asset state changed', source)
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    bpy.ops.wm.open_mainfile(filepath=str(source))
    persisted = signature()
    assert before == persisted, ('persisted asset state changed', source)
    row = {'blend': str(source), 'pass': True, 'geometry_actions_unchanged': True,
           'every_mesh_vertex_loop_hash_unchanged': True, 'rig_actions_frame_unchanged': True,
           'identity_signature': persisted, 'used_image_count': len(packed), 'packed_image_count': len(packed),
           'images': packed, 'source_primary_materials': rows,
           'DCC_material_changes': ['source-primary jacket/pants color transfer', 'sourceBC5 jacket normal XY1.3 then reconstructedZ',
                                    'source jacket metallic-mask primary roughness; pants primary .67',
                                    'captured pants festivalAO reuse via glTF Occlusion; separate from basecolor']}
    (ROOT / 'Exports/MaterialPortability' / (source.stem + '.json')).write_text(json.dumps(row, indent=2), encoding='utf-8')
    results.append(row)
    print('SOURCE_PRIMARY_BLEND_PASS', source.name, len(persisted['meshes']), len(packed), flush=True)
(ROOT / 'Exports/source_character_material_blender_application.json').write_text(json.dumps({'pass': True, 'blends': results}, indent=2), encoding='utf-8')
print('SOURCE_PRIMARY_ALL_BLENDS_PASS', len(results), flush=True)
