"""Independent LBS references and original weight audit for capture selection.

Uses original PAK parser buffers and captured GPU palettes, independently of
Blender edit bones, imported UE bind poses, morphs or DCC evaluated geometry.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
CAP = ROOT / 'Exports/CaptureBuffers'
OUT = CAP / 'IndependentSkinnedMeshes'


def main():
    # The earlier 26 source subsets preserve the initial layer decisions.
    # Actual capture dispatch association excludes both baseline bare-arm subsets.
    # Replace the former prop/teen backpack with capture-proven adult backpack.
    old = json.loads((OUT / 'independent_skinning_report.json').read_text())
    selected = []
    for row in old['rows']:
        if 'backpack' in row['source_folder']:
            continue
        if row['source_folder']=='ellie16_patrol_body' and row['vertices'] in (6234,6270):
            continue
        folder = ROOT / 'Exports/ExactDebug' / row['source_folder']
        doc = json.loads((folder / 'capture.json').read_text())
        mesh = next(m for m in doc['meshes'] if m['name'] == row['source_mesh'])
        selected.append((folder, doc, mesh))
    adult = ROOT / 'Exports/BackpackVariantDebug/ellie_backpack'
    adultdoc = json.loads((adult / 'capture.json').read_text())
    selected.extend((adult, adultdoc, m) for m in adultdoc['meshes'])
    assert len(selected) == 29, len(selected)
    human = np.load(CAP / 'Ellie_Capture_SkinPalette1038.npz')['captured_skin_actor_game']
    hoodie = np.load(CAP / 'Capture_Hoodie_SkinPalette75.npz')['captured_skin_actor_game']
    basis = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float64)
    rows = []
    for folder, doc, mesh in selected:
        z = np.load(folder / mesh['npz'])
        n = mesh['vertex_count']
        stride = mesh['bindings']['pos']['stride'] // 4
        vertices = z['pos_raw'].view('<f4')[:n*stride].reshape(n, stride)[:, :3].astype(np.float64)
        id_dtype = '<u2' if mesh['bindings']['bidx']['type'] == 4 else '<u4'
        weight_dtype = '<f4' if mesh['bindings']['bwgt']['type'] == 0 else '<u4'
        ids_typed = z['bidx_raw'].view(id_dtype)[:n*12].reshape(n,12)
        source_values = z['bwgt_raw'].view(weight_dtype)[:n*12].reshape(n,12)
        ids = ids_typed.astype(np.uint32)
        values = source_values.astype(np.float64)
        active = values > 0
        sums = values.sum(axis=1)
        assert np.isfinite(vertices).all() and np.isfinite(values).all()
        assert (values >= 0).all() and (sums > 0).all(), (folder.name, mesh['name'], np.where(sums <= 0))
        weights = values / sums[:,None]
        owner = 'hoodie_owned78' if doc['pak'] == 'ellie-patrol-hoodie-cloth.pak' else 'human1074'
        palette = hoodie if owner == 'hoodie_owned78' else human
        used_ids = ids[active]
        assert int(used_ids.max()) < len(palette), (mesh['name'], int(used_ids.max()), len(palette))
        homogeneous = np.column_stack([vertices, np.ones(n)])
        skin = palette[ids]
        result = np.einsum('nijk,nk,ni->nj', skin[:,:,:3,:], homogeneous, weights, optimize=True)
        blender = result @ basis.T
        # Captured shader IR: packed uint22 -> float32 -> multiply 0x34800002.
        # The skin shader does NOT renormalize position weights. Float assets
        # retain their original float32 values. Keep this reference separately.
        packed_factor = np.array([0x34800002],dtype='<u4').view('<f4')[0]
        shader_weights = source_values.astype(np.float32)
        if weight_dtype != '<f4':
            shader_weights = shader_weights * packed_factor
        shader_result = np.einsum('nijk,nk,ni->nj', skin[:,:,:3,:], homogeneous,
            shader_weights.astype(np.float64), optimize=True)
        shader_blender = shader_result @ basis.T
        neutral = np.einsum('nj,ni->nj', vertices, weights, optimize=True)
        neutral_error = float(np.abs(neutral-vertices).max())
        # Preserve raw values as typed source arrays: no inferred packed->GPU
        # conversion is asserted to be captured GPU bytes.
        path = OUT / (folder.name+'__'+Path(mesh['npz']).stem+'.npz')
        np.savez_compressed(path, source_vertices_game=vertices,
            captured_skinned_actor_vertices_game=result,
            captured_skinned_actor_vertices_blender=blender,
            source_bone_indices=ids, source_bone_indices_typed=ids_typed,
            source_weight_values_typed=source_values,
            normalized_source_weights=weights,
            original_shader_weights_float32=shader_weights,
            original_shader_weight_skinned_actor_vertices_game=shader_result,
            original_shader_weight_skinned_actor_vertices_blender=shader_blender,
            source_weight_sums=sums)
        repeated = []
        max_unique = 0
        for i, (row_ids, row_active) in enumerate(zip(ids, active)):
            count = int(row_active.sum())
            unique = len(set(int(x) for x in row_ids[row_active]))
            max_unique = max(max_unique, unique)
            if unique != count:
                repeated.append(i)
        weight_format = 'float32' if weight_dtype == '<f4' else 'uint22_packed_decoded_to_uint32'
        row = {'source_folder':folder.name, 'source_pak':doc['pak'], 'source_mesh':mesh['name'],
            'source_capture':str(folder/'capture.json'), 'source_npz':str(folder/mesh['npz']),
            'source_npz_sha256':hashlib.sha256((folder/mesh['npz']).read_bytes()).hexdigest(),
            'material':mesh['material'], 'vertices':n, 'path':str(path),
            'joint_palette_owner':owner, 'validated_captured_palette_matrices':len(palette),
            'source_joint_storage':id_dtype, 'source_weight_storage':weight_format,
            'source_weight_sum_min':float(sums.min()), 'source_weight_sum_max':float(sums.max()),
            'source_zero_weight_vertices':int((sums<=0).sum()),
            'source_nonfinite_weight_components':int((~np.isfinite(values)).sum()),
            'source_negative_weight_components':int((values<0).sum()),
            'source_max_positive_joint_id':int(used_ids.max()),
            'source_positive_influence_count_max':int(active.sum(axis=1).max()),
            'source_unique_joint_influence_count_max':max_unique,
            'source_repeated_positive_joint_vertices':len(repeated),
            'source_repeated_positive_joint_vertex_examples':repeated[:20],
            'source_weight_normalization_max_delta':float(np.abs(weights-values/(1 if weight_dtype=='<f4' else 4194303)).max()),
            'original_shader_vs_DCC_normalized_vertex_max_distance_m':float(np.linalg.norm(shader_result-result,axis=1).max()),
            'pose_bounds_game':[result.min(axis=0).tolist(),result.max(axis=0).tolist()],
            'neutral_weight_roundtrip_max_error':neutral_error}
        rows.append(row)
    total = sum(r['vertices'] for r in rows)
    assert total == 84954, total
    report = {'schema':'tlou2.independent-selected-skin-vertices.v2',
        'selected_character_mesh_count':len(rows), 'selected_character_vertex_count':total,
        'capture_palette_skinned_mesh_count':len(rows), 'capture_palette_skinned_vertex_count':total,
        'source_zero_weight_vertices':sum(r['source_zero_weight_vertices'] for r in rows),
        'all_positive_joints_have_validated_capture_matrices':True,
        'source_format_mesh_counts':{f:sum(r['source_weight_storage']==f for r in rows)for f in sorted(set(r['source_weight_storage']for r in rows))},
        'maximum_neutral_weight_roundtrip_error':max(r['neutral_weight_roundtrip_max_error'] for r in rows),
        'maximum_original_shader_vs_DCC_normalized_vertex_distance_m':max(r['original_shader_vs_DCC_normalized_vertex_max_distance_m']for r in rows),
        'method':'Independent numpy LBS from original PAK source positions, original per-mesh typed weight/joint arrays and captured actor-local GPU palettes. Source float32/u32 records and decoded packed22/10 records are preserved separately. All positive source influences are normalized per vertex for DCC reference; repeated IDs contribute additively. No DCC bind reconstruction is used for reference vertices.',
        'scope':'References validate normalized DCC deformation against captured skin matrices. They do not by themselves prove an asset was bound in an actual GPU draw/dispatch, or prove packed-to-float conversion bit patterns. Separate capture binding report supplies actual dispatch associations.',
        'backpack_selection':'ellie-backpack.pak adult main-human-rig backpack; exact original skin header flag chooses packed22/10 or float32/u32 PER MESH. Supersedes earlier prop and teen diagnostic references.',
        'source_format_evidence':str(adult/'skin_format_headers.json'),
        'original_shader_weight_policy':'Captured packed skin IR converts weight22 to float32 and multiplies factor bits0x34800002 (float32(1/4194303)); float32 source weights remain original. Position weights are not renormalized. The NPZ original_shader_weight_* arrays use those float32 weights with float64 mathematical LBS; operation-order GPU rounding is not asserted bit exact.',
        'original_shader_weight_evidence':str(CAP/'Shaders/chunk_47335.asm.txt'),
        'capture_selection_evidence':str(ROOT/'Content/TLOU2/Reports/CAPTURE_MESH_SOURCE_BINDING_VALIDATION.json'),
        'excluded_baseline_bare_arms':'ellie16_patrol_hands subsets6234/6270 have no actual captured dispatch or captured geometry match; preserved as optional raw source, omitted from final capture-visible character.',
        'rows':rows}
    out = OUT / 'selected29_independent_skinning_report.json'
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines = ['# Independent selected character skin and weight audit', '',
        f'{len(rows)} selected meshes; {total:,} vertices. Every vertex has positive original source weights and all weighted joints map to validated capture matrices.', '',
        report['method'], '', report['scope'], '',
        '| Package | Vertices | Weight format | Highest joint | Zero weights | Repeated joint vertices |',
        '|---|---:|---|---:|---:|---:|']
    lines.extend(f"| {r['source_pak']} | {r['vertices']} | {r['source_weight_storage']} | {r['source_max_positive_joint_id']} | {r['source_zero_weight_vertices']} | {r['source_repeated_positive_joint_vertices']} |" for r in rows)
    lines.extend(['', f"Maximum neutral-weight roundtrip error: {report['maximum_neutral_weight_roundtrip_error']:.9g} meters.", '', report['backpack_selection']])
    (OUT/'SELECTED29_SKIN_WEIGHT_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))


if __name__ == '__main__':
    main()
