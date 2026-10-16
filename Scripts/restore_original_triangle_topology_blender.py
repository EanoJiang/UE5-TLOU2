"""Restore original repeated jacket triangles without replacing mesh datablocks.

Usage: blender --background --python this_script.py -- path/to/file.blend
Only the 29 capture-selected character meshes are inspected. The two jacket
meshes expand their existing loop/polygon arrays in place; source triangle order
is restored. Vertices, skin groups, shape keys, actions, bones and stage objects
are retained. Pre-restoration corner normals are deliberately stored as custom
split normals so repeated raster primitives do not change smooth shading.
Never calls Mesh.validate(), which would remove the original duplicate faces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
REFERENCE = ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json'
REST = ROOT/'Exports/Ellie_AugmentedBindRest_SourceMatrices.json'
ALLOWED = {'patrol_jacket__lod0_LODShape0_shader1_merged_partition0',
           'patrol_jacket__lod0_LODShape0_shader1_merged_partition1'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def array_digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def read_collection(collection, field, width, dtype=np.float32):
    result = np.empty(len(collection) * width, dtype=dtype)
    if len(collection):
        collection.foreach_get(field, result)
    return result.reshape(len(collection), width) if width != 1 else result


def attribute_snapshot(mesh):
    result = {}
    for attribute in mesh.attributes:
        if not len(attribute.data):
            continue
        item = attribute.data[0]
        candidates = [field for field in ('value', 'vector', 'color')
                      if field in item.bl_rna.properties and item.bl_rna.properties[field].type in ('FLOAT', 'INT', 'BOOLEAN')]
        if not candidates:
            raise RuntimeError('Unsupported attribute storage; refusing mutation: ' + attribute.name)
        field = candidates[0]
        prop = item.bl_rna.properties[field]
        width = prop.array_length if prop.is_array else 1
        dtype = np.float32 if prop.type == 'FLOAT' else np.int32 if prop.type == 'INT' else np.bool_
        result[attribute.name] = {'domain': attribute.domain, 'type': attribute.data_type,
                                 'field': field, 'width': width,
                                 'values': read_collection(attribute.data, field, width, dtype)}
    return result


def action_signature():
    actions = []
    for action in bpy.data.actions:
        curves = []
        if hasattr(action, 'fcurves'):
            curves.extend(action.fcurves)
        else:
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        curves.extend(bag.fcurves)
        actions.append({'name': action.name, 'slots': [(s.identifier, s.target_id_type) for s in getattr(action, 'slots', [])],
                        'curves': [(c.data_path, c.array_index, c.extrapolation,
                                    [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right),
                                      k.interpolation, k.easing, k.handle_left_type, k.handle_right_type)
                                     for k in c.keyframe_points]) for c in curves]})
    return digest(actions)


def skin_signature(obj):
    h = hashlib.sha256()
    h.update(json.dumps([g.name for g in obj.vertex_groups]).encode())
    for vertex in obj.data.vertices:
        h.update(struct.pack('<II', vertex.index, len(vertex.groups)))
        for group in vertex.groups:
            h.update(struct.pack('<If', group.group, group.weight))
    return h.hexdigest()


def shape_signature(mesh):
    keys = mesh.shape_keys
    if not keys:
        return None
    rows = []
    for key in keys.key_blocks:
        rows.append((key.name, key.value, key.mute, key.slider_min, key.slider_max,
                     key.vertex_group, key.relative_key.name,
                     array_digest(read_collection(key.data, 'co', 3))))
    return digest({'keys': rows, 'relative': keys.use_relative,
                   'action': keys.animation_data.action.name if keys.animation_data and keys.animation_data.action else None})


def bone_signature():
    return digest([(o.name, tuple(tuple(row) for row in o.matrix_world),
                    [(b.name, b.parent.name if b.parent else None, tuple(tuple(row) for row in b.matrix_local),
                      tuple(tuple(row) for row in o.pose.bones[b.name].matrix)) for b in o.data.bones])
                   for o in bpy.data.objects if o.type == 'ARMATURE'])


def immutable_mesh_signature(obj):
    mesh = obj.data
    return {'vertices': len(mesh.vertices), 'positions_sha256': array_digest(read_collection(mesh.vertices, 'co', 3)),
            'skin_sha256': skin_signature(obj), 'shape_sha256': shape_signature(mesh),
            'materials': [m.name if m else None for m in mesh.materials],
            'object_transform': [list(row) for row in obj.matrix_world],
            'uv_state': [(layer.name, layer.active_render, layer.active_clone) for layer in mesh.uv_layers],
            'uv_active_index': mesh.uv_layers.active_index,
            'modifiers': [(m.name, m.type, m.object.name if m.type == 'ARMATURE' and m.object else None) for m in obj.modifiers]}


def current_faces(mesh):
    totals = read_collection(mesh.polygons, 'loop_total', 1, np.int32)
    starts = read_collection(mesh.polygons, 'loop_start', 1, np.int32)
    assert np.all(totals == 3) and np.array_equal(starts, np.arange(len(mesh.polygons)) * 3)
    return read_collection(mesh.loops, 'vertex_index', 1, np.int32).reshape(-1, 3)


def original_data(row):
    raw_path = Path(row['source_npz'])
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == row['source_npz_sha256']
    metadata = json.loads(Path(row['source_capture']).read_text())
    source = next(m for m in metadata['meshes'] if m['name'] == row['source_mesh'])
    with np.load(raw_path) as archive:
        assert source['index_type'] in (4, 5)
        indices = archive['indices_raw'].view('<u2' if source['index_type'] == 4 else '<u4')[:source['count']].astype(np.int32)
        stride = source['bindings']['pos']['stride'] // 4
        positions = archive['pos_raw'].view('<f4')[:row['vertices']*stride].reshape(row['vertices'], stride)[:, :3].copy()
    with np.load(row['path']) as archive:
        ids = archive['source_bone_indices'].copy()
        weights = archive['normalized_source_weights'].copy()
    assert len(indices) == source['count'] and len(indices) % 3 == 0 and (indices < row['vertices']).all()
    # Original game (x,y,z) -> Blender (x,-z,y), all in meters.
    positions = positions[:, [0, 2, 1]] * np.array((1, -1, 1), dtype=np.float32)
    return indices.reshape(-1, 3), positions, ids, weights


def verify_named_skin(obj, ids, weights, bone_names):
    group_names = [g.name for g in obj.vertex_groups]
    maximum = 0.0
    strict_float32_equal = True
    for vertex, source_ids, source_weights in zip(obj.data.vertices, ids, weights):
        expected = {}
        for bone, weight in zip(source_ids, source_weights):
            if weight > 0:
                name = bone_names[int(bone)]
                expected[name] = expected.get(name, 0.0) + float(weight)
        expected = {name: float(np.float32(weight)) for name, weight in expected.items()}
        actual = {group_names[g.group]: float(g.weight) for g in vertex.groups if g.weight > 0}
        errors = [abs(actual.get(name, 0) - expected.get(name, 0)) for name in expected.keys() | actual.keys()]
        error = max(errors, default=0.0)
        maximum = max(maximum, error)
        strict_float32_equal &= error == 0
    assert maximum < 2e-7, (obj.name, maximum)
    return {'source_named_weight_max_error': maximum, 'source_named_weights_float32_exact': strict_float32_equal}


def restore_mesh(obj, target_faces):
    mesh = obj.data
    before_faces = current_faces(mesh)
    target_counter = Counter(map(tuple, target_faces))
    before_counter = Counter(map(tuple, before_faces))
    assert set(before_counter) == set(target_counter), 'Missing unique geometry cannot be restored as duplicate primitives'
    assert not (before_counter - target_counter), 'Existing mesh contains triangles absent from the original'
    missing = len(target_faces) - len(before_faces)
    if missing == 0 and np.array_equal(before_faces, target_faces):
        return {'changed': False, 'before_triangles': len(before_faces), 'after_triangles': len(before_faces), 'added_duplicate_triangles': 0}
    assert obj['source_submesh'] in ALLOWED and missing in (0, 56, 452)
    old_index_by_face = defaultdict(list)
    for index, face in enumerate(before_faces):
        old_index_by_face[tuple(face)].append(index)
    uses = Counter()
    polygon_map = []
    for face in target_faces:
        key = tuple(face)
        candidates = old_index_by_face[key]
        polygon_map.append(candidates[min(uses[key], len(candidates)-1)])
        uses[key] += 1
    polygon_map = np.array(polygon_map, dtype=np.int32)
    corner_map = (polygon_map[:, None]*3 + np.arange(3)).ravel()
    attributes = attribute_snapshot(mesh)
    normals = read_collection(mesh.corner_normals, 'vector', 3)
    old_custom_normals = mesh.has_custom_normals
    material_ids = read_collection(mesh.polygons, 'material_index', 1, np.int32)
    smooth = read_collection(mesh.polygons, 'use_smooth', 1, np.bool_)
    original_mesh_pointer = mesh.as_pointer()
    original_vertex_count = len(mesh.vertices)
    original_edge_count = len(mesh.edges)
    mesh.loops.add(missing*3)
    mesh.polygons.add(missing)
    mesh.polygons.foreach_set('loop_start', np.arange(len(target_faces), dtype=np.int32)*3)
    mesh.polygons.foreach_set('vertices', target_faces.ravel())
    for name, snapshot in attributes.items():
        if snapshot['domain'] not in ('CORNER', 'FACE'):
            continue
        mapping = corner_map if snapshot['domain'] == 'CORNER' else polygon_map
        values = np.ascontiguousarray(snapshot['values'][mapping])
        mesh.attributes[name].data.foreach_set(snapshot['field'], values.ravel())
    mesh.polygons.foreach_set('material_index', material_ids[polygon_map])
    mesh.polygons.foreach_set('use_smooth', smooth[polygon_map])
    # Every restored edge already exists; never rebuild or replace edge data.
    mesh.update(calc_edges=False, calc_edges_loose=False)
    expected_normals = normals[corner_map]
    natural_normals = read_collection(mesh.corner_normals, 'vector', 3)
    natural_normal_error = float(np.linalg.norm(natural_normals - expected_normals, axis=1).max())
    mesh.normals_split_custom_set(expected_normals.tolist())
    mesh.update(calc_edges=False, calc_edges_loose=False)
    assert mesh.as_pointer() == original_mesh_pointer
    assert len(mesh.vertices) == original_vertex_count and len(mesh.edges) == original_edge_count
    assert np.array_equal(current_faces(mesh), target_faces), 'Original ordered triangle index sequence was not restored'
    after_attributes = attribute_snapshot(mesh)
    checked = []
    for name, snapshot in attributes.items():
        # Custom-normal storage is intentionally regenerated from pre-restoration
        # corner vectors to retain shading as the face-averaging basis changes.
        if 'custom_normal' in name:
            continue
        mapping = corner_map if snapshot['domain'] == 'CORNER' else polygon_map if snapshot['domain'] == 'FACE' else None
        expected = snapshot['values'][mapping] if mapping is not None else snapshot['values']
        assert name in after_attributes and np.array_equal(after_attributes[name]['values'], expected), name
        checked.append(name)
    actual_normals = read_collection(mesh.corner_normals, 'vector', 3)
    normal_errors = np.linalg.norm(actual_normals - expected_normals, axis=1)
    normal_error = float(normal_errors.max())
    # Blender encodes custom normals in a compact angular representation.
    assert normal_error < 0.002, ('custom normal encoding error', normal_error)
    assert mesh.has_custom_normals
    mesh.calc_loop_triangles()
    assert len(mesh.loop_triangles) == len(target_faces)
    return {'changed': True, 'before_triangles': len(before_faces), 'after_triangles': len(target_faces),
            'added_duplicate_triangles': missing, 'ordered_original_indices_exact': True,
            'mesh_datablock_retained_in_place': True, 'vertices_and_edges_retained': True,
            'remapped_attributes_checked_exact': checked, 'original_had_custom_normals': old_custom_normals,
            'shading_policy': 'Pre-restoration corner normal vectors explicitly retained as custom split normals; duplicate loops copy the matching original face.',
            'custom_corner_normal_max_vector_encoding_error': normal_error,
            'custom_corner_normal_mean_vector_encoding_error': float(normal_errors.mean()),
            'custom_corner_normal_p99_vector_encoding_error': float(np.quantile(normal_errors, .99)),
            'computed_corner_normal_max_error_without_shading_preservation': natural_normal_error,
            'custom_corner_normal_vector_encoding_tolerance': 0.002,
            'new_attributes': sorted(set(after_attributes)-set(attributes))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('blend', type=Path)
    parser.add_argument('--export-test-glb', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    blend = args.blend.resolve()
    assert blend.is_file() and blend.suffix.lower() == '.blend'
    source_sha256 = hashlib.sha256(blend.read_bytes()).hexdigest()
    reference = json.loads(REFERENCE.read_text())
    assert len(reference['rows']) == 29
    rest_rows = json.loads(REST.read_text())['rows']
    human_names = [r['bone_name'] for r in rest_rows if r.get('rig_owner') not in ('hoodie', 'backpack')]
    hoodie_names = [r['bone_name'] for r in sorted((r for r in rest_rows if r.get('rig_owner') == 'hoodie'), key=lambda r: r['owned_source_bone_index'])]
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    matched = []
    for row in reference['rows']:
        matches = [o for o in bpy.data.objects if o.type == 'MESH' and o.get('source_submesh') == row['source_mesh']
                   and Path(o.get('source_pak', '')).name == row['source_pak'] and len(o.data.vertices) == row['vertices']]
        assert len(matches) == 1, (row['source_mesh'], [o.name for o in matches])
        matched.append((row, matches[0]))
    assert len({o.as_pointer() for _, o in matched}) == 29
    selected = {o.as_pointer() for _, o in matched}
    other_meshes = {o.name: immutable_mesh_signature(o) | {'faces_sha256': array_digest(read_collection(o.data.loops, 'vertex_index', 1, np.int32))}
                    for o in bpy.data.objects if o.type == 'MESH' and o.as_pointer() not in selected}
    immutable_before = {o.name: immutable_mesh_signature(o) for _, o in matched}
    actions_before = action_signature()
    bones_before = bone_signature()
    rows = []
    for source, obj in matched:
        target, positions, ids, weights = original_data(source)
        actual_positions = read_collection(obj.data.vertices, 'co', 3)
        assert np.array_equal(actual_positions, positions), (obj.name, 'bind positions differ from original')
        names = hoodie_names if source['joint_palette_owner'] == 'hoodie_owned78' else human_names
        source_skin = verify_named_skin(obj, ids, weights, names)
        entry = restore_mesh(obj, target)
        assert immutable_mesh_signature(obj) == immutable_before[obj.name], (obj.name, 'immutable mesh data changed')
        assert np.array_equal(current_faces(obj.data), target)
        assert np.array_equal(read_collection(obj.data.vertices, 'co', 3)[target], positions[target])
        entry.update({'mesh': obj.name, 'source_mesh': source['source_mesh'], 'vertices': len(obj.data.vertices),
                      'source_pak': source['source_pak'], 'source_npz_sha256': source['source_npz_sha256'],
                      'original_triangle_coordinate_and_named_weight_multiset_exact': source_skin['source_named_weights_float32_exact'],
                      'position_skin_shape_material_uv_state_signatures_unchanged': True, **source_skin})
        assert entry['original_triangle_coordinate_and_named_weight_multiset_exact']
        rows.append(entry)
    bpy.context.view_layer.update()
    assert action_signature() == actions_before, 'Animation action content changed'
    assert bone_signature() == bones_before, 'Bone reference/pose transforms changed'
    for obj in bpy.data.objects:
        if obj.name in other_meshes:
            signature = immutable_mesh_signature(obj) | {'faces_sha256': array_digest(read_collection(obj.data.loops, 'vertex_index', 1, np.int32))}
            assert signature == other_meshes[obj.name], ('stage/other mesh changed', obj.name)
    assert sum(r['after_triangles'] for r in rows) == 117459
    assert sum(r['vertices'] for r in rows) == 84954
    assert sum(r['added_duplicate_triangles'] for r in rows) in (0, 508)
    report = {'blend': str(blend), 'input_blend_sha256': source_sha256, 'selected_character_meshes': len(rows),
              'vertices': sum(r['vertices'] for r in rows), 'triangles_before': sum(r['before_triangles'] for r in rows),
              'triangles_after': sum(r['after_triangles'] for r in rows),
              'added_duplicate_triangles': sum(r['added_duplicate_triangles'] for r in rows),
              'changed_meshes': [r['mesh'] for r in rows if r['changed']],
              'all_original_triangle_orders_exact': True, 'all_position_skin_shape_signatures_unchanged': True,
              'all_source_named_weights_float32_exact': True, 'actions_unchanged': True, 'bone_transforms_unchanged': True,
              'stage_and_other_meshes_unchanged': True, 'other_mesh_count': len(other_meshes), 'pass': True, 'rows': rows}
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report['output_blend_sha256'] = hashlib.sha256(blend.read_bytes()).hexdigest()
    if args.export_test_glb:
        bpy.ops.object.select_all(action='DESELECT')
        for _, obj in matched:
            obj.select_set(True)
        arm = next(m.object for _, o in matched for m in o.modifiers if m.type == 'ARMATURE' and m.object)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.gltf(filepath=str(args.export_test_glb.resolve()), export_format='GLB', use_selection=True,
                                  export_animations=True, export_all_influences=True)
        assert all(np.array_equal(current_faces(o.data), original_data(r)[0]) for r, o in matched), 'Exporter normalized restored topology'
        report['test_glb'] = str(args.export_test_glb.resolve())
        report['test_export_preserved_mesh_topology'] = True
    out = ROOT/'Exports/TopologyRestoration'/(blend.stem+'.json')
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('ORIGINAL_TOPOLOGY_RESTORED '+json.dumps({k: v for k, v in report.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
