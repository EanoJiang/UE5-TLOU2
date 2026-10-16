"""Hash-bound FBX binary topology/skin and independent Blender reimport checks.

Usage: blender --background --python this_script.py [-- file.fbx ...]
Binary PolygonVertexIndex arrays are authoritative for triangle multiplicity;
Blender's FBX importer may normalize repeated faces on reimport. That separate
diagnostic never substitutes for checking the actual exported FBX bytes.
"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix
from io_scene_fbx import parse_fbx

ROOT = Path('D:/TLOU2_UE5_8_Codex')
LABELS = ('Ellie_Patrol_Catalog_CaptureMatched', 'Ellie_Patrol_CapturedSkinPose',
          'Ellie_Patrol_Original_0FW', 'Ellie16_Patrol_OriginalViewerPose')


def text(value):
    return value.decode('utf-8') if isinstance(value, bytes) else value


def child(element, name):
    return next(e for e in element.elems if e.id == name)


def model_properties(model):
    return {text(e.props[0]): text(e.props[-1]) for e in child(model, b'Properties70').elems if e.id == b'P'}


def source_data(row, human, hoodie):
    assert hashlib.sha256(Path(row['source_npz']).read_bytes()).hexdigest() == row['source_npz_sha256']
    meta = json.loads(Path(row['source_capture']).read_text())
    mesh = next(m for m in meta['meshes'] if m['name'] == row['source_mesh'])
    with np.load(row['source_npz']) as archive:
        stride = mesh['bindings']['pos']['stride'] // 4
        positions = archive['pos_raw'].view('<f4')[:row['vertices']*stride].reshape(row['vertices'], stride)[:, :3].copy()
        indices = archive['indices_raw'].view('<u2' if mesh['index_type'] == 4 else '<u4')[:mesh['count']].copy()
    positions = positions[:, [0, 2, 1]].astype(np.float64) * (1, -1, 1)
    names = hoodie if row['joint_palette_owner'] == 'hoodie_owned78' else human
    with np.load(row['path']) as archive:
        ids = archive['source_bone_indices']
        weights = archive['normalized_source_weights']
        bindings = []
        for vertex_ids, vertex_weights in zip(ids, weights):
            value = {}
            for index, weight in zip(vertex_ids, vertex_weights):
                if weight > 0:
                    name = names[int(index)]
                    value[name] = value.get(name, 0.0) + float(weight)
            bindings.append({name: float(np.float32(weight)) for name, weight in value.items()})
    return {'positions': positions, 'indices': indices, 'bindings': bindings, 'row': row}


def binding_error(actual, expected):
    assert len(actual) == len(expected)
    maximum = 0.0
    active = 0
    sum_error = 0.0
    for got, want in zip(actual, expected):
        active = max(active, len(got))
        sum_error = max(sum_error, abs(sum(got.values())-1))
        maximum = max(maximum, max((abs(got.get(n, 0)-want.get(n, 0)) for n in got.keys() | want.keys()), default=0.0))
    return maximum, active, sum_error


def binary_check(path, sources):
    tree, version = parse_fbx.parse(str(path))
    elements = child(tree, b'Objects').elems
    by_id = {e.props[0]: e for e in elements}
    parents, children = defaultdict(list), defaultdict(list)
    for link in child(tree, b'Connections').elems:
        if link.id == b'C' and link.props[0] == b'OO':
            parents[link.props[1]].append(link.props[2])
            children[link.props[2]].append(link.props[1])
    rows = []
    matched = set()
    for geometry in (e for e in elements if e.id == b'Geometry' and e.props[2] == b'Mesh'):
        models = [by_id[i] for i in parents[geometry.props[0]] if i in by_id and by_id[i].id == b'Model']
        assert len(models) == 1
        properties = model_properties(models[0])
        key = (Path(properties['source_pak']).name, properties['source_submesh'])
        assert key in sources and key not in matched
        matched.add(key)
        source = sources[key]
        positions = np.array(child(geometry, b'Vertices').props[0], dtype=np.float64).reshape(-1, 3)
        encoded = np.array(child(geometry, b'PolygonVertexIndex').props[0], dtype=np.int64)
        assert len(encoded) % 3 == 0 and np.array_equal(np.flatnonzero(encoded < 0), np.arange(2, len(encoded), 3))
        indices = np.where(encoded < 0, -encoded-1, encoded)
        positions_exact = np.array_equal(positions, source['positions'])
        indices_exact = np.array_equal(indices, source['indices'])
        actual = [{} for _ in range(len(positions))]
        skins = [by_id[i] for i in children[geometry.props[0]] if i in by_id and by_id[i].id == b'Deformer' and by_id[i].props[2] == b'Skin']
        assert len(skins) == 1
        clusters = [by_id[i] for i in children[skins[0].props[0]] if i in by_id and by_id[i].id == b'Deformer' and by_id[i].props[2] == b'Cluster']
        for cluster in clusters:
            if not any(e.id == b'Indexes' for e in cluster.elems):
                assert not any(e.id == b'Weights' for e in cluster.elems)
                continue
            bones = [by_id[i] for i in children[cluster.props[0]] if i in by_id and by_id[i].id == b'Model']
            assert len(bones) == 1
            name = text(bones[0].props[1]).split('\x00\x01', 1)[0]
            ids = child(cluster, b'Indexes').props[0]
            weights = child(cluster, b'Weights').props[0]
            assert len(ids) == len(weights)
            for index, weight in zip(ids, weights):
                assert 0 <= index < len(actual) and np.isfinite(weight) and weight >= 0
                if weight > 0:
                    actual[index][name] = actual[index].get(name, 0.0) + float(weight)
        weight_error, influences, sum_error = binding_error(actual, source['bindings'])
        rows.append({'source_pak': key[0], 'source_mesh': key[1], 'vertices': len(positions),
                     'triangles': len(indices)//3, 'source_triangles': len(source['indices'])//3,
                     'ordered_original_control_point_positions_exact': positions_exact,
                     'ordered_original_triangle_indices_exact': indices_exact,
                     'source_named_float32_skin_max_error': weight_error,
                     'maximum_positive_influences': influences, 'weight_sum_max_error': sum_error,
                     'pass': positions_exact and indices_exact and weight_error < 2e-7 and sum_error < 2e-6})
    assert matched == set(sources)
    return {'fbx_version': version, 'mesh_count': len(rows), 'vertices': sum(r['vertices'] for r in rows),
            'triangles': sum(r['triangles'] for r in rows), 'source_triangles': sum(r['source_triangles'] for r in rows),
            'maximum_source_named_skin_error': max(r['source_named_float32_skin_max_error'] for r in rows),
            'pass': all(r['pass'] for r in rows), 'meshes': rows}


def reimport_check(path, sources, rest_rows):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=True, use_custom_props=True,
                              automatic_bone_orientation=False, use_prepost_rot=True)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(arms) == 1 and len(arms[0].data.bones) == 1152 and len(meshes) == 29
    arm = arms[0]
    matrix_error = 0.0
    for row in rest_rows:
        actual = arm.matrix_world @ arm.data.bones[row['bone_name']].matrix_local
        expected = Matrix(row['global_matrix_blender_meters'])
        matrix_error = max(matrix_error, max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4)))
    rows = []
    matched = set()
    for obj in meshes:
        key = (Path(obj['source_pak']).name, obj['source_submesh'])
        assert key in sources and key not in matched
        matched.add(key)
        source = sources[key]
        positions = np.array([v.co[:] for v in obj.data.vertices], dtype=np.float64)
        assert positions.shape == source['positions'].shape
        position_error = float(np.abs(positions-source['positions']).max())
        names = [group.name for group in obj.vertex_groups]
        actual = [{names[g.group]: float(g.weight) for g in v.groups if g.weight > 0} for v in obj.data.vertices]
        weight_error, influences, sum_error = binding_error(actual, source['bindings'])
        obj.data.calc_loop_triangles()
        rows.append({'mesh': obj.name, 'source_mesh': key[1], 'vertices': len(positions),
                     'imported_triangles': len(obj.data.loop_triangles), 'source_triangles': len(source['indices'])//3,
                     'position_max_error_m': position_error, 'source_named_skin_max_error': weight_error,
                     'maximum_positive_influences': influences, 'weight_sum_max_error': sum_error,
                     'shape_keys': [k.name for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
                     'custom_normals': obj.data.has_custom_normals,
                     'armature_modifier_correct': any(m.type == 'ARMATURE' and m.object == arm for m in obj.modifiers),
                     'pass': position_error < 1e-7 and weight_error < 2e-7 and sum_error < 2e-6 and any(m.type == 'ARMATURE' and m.object == arm for m in obj.modifiers)})
    assert matched == set(sources)
    action = arm.animation_data.action if arm.animation_data else None
    return {'armatures': len(arms), 'bones': len(arm.data.bones), 'mesh_count': len(rows),
            'vertices': sum(r['vertices'] for r in rows), 'imported_triangles': sum(r['imported_triangles'] for r in rows),
            'reference_matrix_max_error': matrix_error, 'source_named_skin_max_error': max(r['source_named_skin_max_error'] for r in rows),
            'animation_action': action.name if action else None,
            'animation_frame_range': list(action.frame_range) if action else None,
            'normalization_note': 'Blender FBX reimport may remove repeated faces; actual binary topology is checked separately and remains authoritative.',
            'pass': all(r['pass'] for r in rows) and matrix_error < 1e-4, 'meshes': rows}


def main():
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    paths = [Path(p).resolve() for p in args] if args else [ROOT/'Exports'/(label+'.fbx') for label in LABELS]
    reference = json.loads((ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json').read_text())
    rest = json.loads((ROOT/'Exports/Ellie_AugmentedBindRest_SourceMatrices.json').read_text())
    human = [r['bone_name'] for r in rest['rows'] if r.get('rig_owner') not in ('hoodie', 'backpack')]
    hoodie = [r['bone_name'] for r in sorted((r for r in rest['rows'] if r.get('rig_owner') == 'hoodie'), key=lambda r: r['owned_source_bone_index'])]
    sources = {(r['source_pak'], r['source_mesh']): source_data(r, human, hoodie) for r in reference['rows']}
    files = []
    for path in paths:
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        source_blend = ROOT/'Blender'/(path.stem+'.blend')
        binary = binary_check(path, sources)
        imported = reimport_check(path, sources, rest['rows'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before, 'FBX changed during verification'
        files.append({'file': str(path), 'sha256': before, 'bytes': path.stat().st_size,
                      'source_blend': str(source_blend), 'source_blend_sha256': hashlib.sha256(source_blend.read_bytes()).hexdigest(),
                      'binary': binary, 'blender_reimport': imported, 'pass': binary['pass'] and imported['pass']})
        print('CANONICAL_FBX_FILE '+json.dumps({k: v for k, v in files[-1].items() if k not in ('binary', 'blender_reimport')}), flush=True)
    report = {'files': files, 'file_count': len(files), 'source_meshes_per_file': 29, 'source_vertices_per_file': 84954,
              'source_triangles_per_file': 117459, 'pass': all(f['pass'] for f in files),
              'method': 'Independent FBX binary control-point/ordered-index/named-cluster-weight inspection plus separate Blender reimport rig, bind-matrix and skin verification; SHA256 binds each exported file and its restored source Blend.',
              'topology_note': 'Binary triangle arrays prove original draw multiplicity even when a DCC importer chooses to normalize duplicate faces.'}
    out = ROOT/'Exports/canonical_fbx_fidelity_validation.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CANONICAL_FBX_FIDELITY '+json.dumps({k: v for k, v in report.items() if k != 'files'}), flush=True)
    if not report['pass']:
        raise RuntimeError('Canonical FBX binary/reimport fidelity verification failed')


if __name__ == '__main__':
    main()
