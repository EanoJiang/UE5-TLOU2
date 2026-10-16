"""Export only the restored neutral/captured body chunks; source Blends stay untouched."""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix
from io_scene_fbx import parse_fbx

ROOT = Path('D:/TLOU2_UE5_8_Codex')
PIPELINES = [('Ellie_Patrol_Catalog_CaptureMatched', 'CaptureMatchedChunks', 'capture_matched_chunk_manifest.json'),
             ('Ellie_Patrol_CapturedSkinPose', 'CapturedSkinPoseChunks', 'captured_skin_pose_chunk_manifest.json')]


def child(element, name):
    return next(e for e in element.elems if e.id == name)


def binary_topology(path, originals):
    tree, _ = parse_fbx.parse(str(path))
    objects = child(tree, b'Objects').elems
    models = {e.props[0]: e for e in objects if e.id == b'Model'}
    connections = child(tree, b'Connections').elems
    rows = []
    for geometry in (e for e in objects if e.id == b'Geometry' and e.props[2] == b'Mesh'):
        layer_names = {e.id for e in geometry.elems}
        assert {b'LayerElementNormal', b'LayerElementTangent', b'LayerElementBinormal'} <= layer_names, 'Normals/tangent/binormal layers must exist before UE import'
        parents = [models[e.props[2]] for e in connections if e.id == b'C' and e.props[0] == b'OO'
                   and e.props[1] == geometry.props[0] and e.props[2] in models]
        assert len(parents) == 1
        properties = {e.props[0].decode(): e.props[-1] for e in child(parents[0], b'Properties70').elems if e.id == b'P'}
        name = properties['source_submesh'].decode()
        expected = originals[name]
        encoded = np.array(child(geometry, b'PolygonVertexIndex').props[0], dtype=np.int64)
        assert np.array_equal(np.flatnonzero(encoded < 0), np.arange(2, len(encoded), 3))
        indices = np.where(encoded < 0, -encoded-1, encoded)
        assert np.array_equal(indices, expected), name
        rows.append({'source_mesh': name, 'triangles': len(indices)//3, 'ordered_original_triangle_indices_exact': True,
                     'normal_tangent_binormal_layers_present': True})
    assert len(rows) == 9 and sum(r['triangles'] for r in rows) == 46249
    return rows


def main():
    references = json.loads((ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json').read_text())['rows']
    outputs = []
    for label, folder, manifest_name in PIPELINES:
        source = ROOT/'Blender'/(label+'.blend')
        before_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        bpy.ops.wm.open_mainfile(filepath=str(source))
        arm = bpy.data.objects['SK_Ellie_Patrol_Exact']
        arm.animation_data_clear()
        for bone in arm.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
        meshes = [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers)]
        ns = {'__name__': 'body_chunk_preparation'}
        script = ROOT/'Scripts/make_pruned_armature_fbx.py'
        established = script.read_text()
        needle = "primary_bone_axis='Y', secondary_bone_axis='X')"
        assert established.count(needle) == 1
        # The controlled body reimport disables tangent recomputation, so export
        # tangent/binormal data explicitly rather than relying on FBX defaults.
        established = established.replace(needle, "primary_bone_axis='Y', secondary_bone_axis='X', use_tspace=True)")
        exec(compile(established, str(script), 'exec'), ns)
        body = ns['mesh_chunks'](meshes)['body_clothing']
        assert len(body) == 9
        originals = {}
        for obj in body:
            ref = next(r for r in references if r['source_mesh'] == obj['source_submesh'] and r['source_pak'] == obj['source_pak'])
            metadata = json.loads(Path(ref['source_capture']).read_text())
            raw_mesh = next(m for m in metadata['meshes'] if m['name'] == ref['source_mesh'])
            with np.load(ref['source_npz']) as archive:
                originals[ref['source_mesh']] = archive['indices_raw'].view('<u2' if raw_mesh['index_type'] == 4 else '<u4')[:raw_mesh['count']].copy()
            if obj.data.shape_keys:
                # Temporary export state only: retain every morph delta while
                # writing bind geometry rather than the active captured pose.
                obj.data.shape_keys.animation_data_clear()
                for key in obj.data.shape_keys.key_blocks:
                    if key.name != 'Basis':
                        key.value = 0
        bpy.context.view_layer.update()
        ns['OUT_DIR'] = str(ROOT/'Exports'/folder)
        result = ns['clone_chunk']('body_clothing', body, arm)
        path = Path(result['fbx'])
        checked = binary_topology(path, originals)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == before_sha
        manifest_path = ROOT/'Exports'/manifest_name
        manifest = json.loads(manifest_path.read_text())
        manifest['chunks']['body_clothing'] = result
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        outputs.append({'source_blend': str(source), 'source_blend_sha256': before_sha,
                        'fbx': str(path), 'fbx_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'manifest': str(manifest_path), 'source_blend_unchanged': True,
                        'meshes': len(checked), 'triangles': sum(r['triangles'] for r in checked),
                        'ordered_original_triangle_indices_exact': True, 'topology': checked, 'pass': True})
    report = {'pass': True, 'body_only': True, 'outputs': outputs,
              'policy': 'Reuse established chunk exporter settings with use_tspace=True so imported custom normals and tangent/binormal layers can all be retained. Only neutral/captured body FBXs and their existing manifest entries are refreshed; source Blends/actions are never saved.'}
    (ROOT/'Exports/restored_body_chunk_export_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('RESTORED_BODY_CHUNKS '+json.dumps(report))


if __name__ == '__main__':
    main()
