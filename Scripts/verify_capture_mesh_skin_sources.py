"""Associate original character subsets with actual captured skin dispatches.

Exact source weight/bone bytes distinguish same-count meshes. VSharp candidates
are retained as a separate historical-upload observation, never a draw claim.
"""
from pathlib import Path
import collections
import hashlib
import json
import struct
import numpy as np
from ngfx_resource_reader import read_resource

ROOT = Path('D:/TLOU2_UE5_8_Codex')
EXPORT = ROOT / 'Exports'
CAP = EXPORT / 'CaptureBuffers'
REPORT = ROOT / 'Content/TLOU2/Reports'


def canonical_skin(ids, weights, encoding):
    """Hash meaningful original ordered records; omit zero-weight padding."""
    result = bytearray()
    count = 0
    for row_ids, row_weights in zip(ids, weights):
        active = row_weights != 0
        number = int(active.sum())
        result.extend(struct.pack('<I', number))
        for joint, weight in zip(row_ids[active], row_weights[active]):
            if encoding == 'packed22weight10joint':
                result.extend(struct.pack('<I', int(weight) | (int(joint) << 22)))
            else:
                result.extend(struct.pack('<fI', float(weight), int(joint)))
        count += number
    return hashlib.sha256(result).hexdigest(), count


def source_skin(folder, mesh):
    z = np.load(folder / mesh['npz'])
    n = mesh['vertex_count']
    id_type = '<u2' if mesh['bindings']['bidx']['type'] == 4 else '<u4'
    ids = z['bidx_raw'].view(id_type)[:n * 12].reshape(n, 12).astype('<u4')
    encoding = 'float32weight_uint32joint' if mesh['bindings']['bwgt']['type'] == 0 else 'packed22weight10joint'
    weight_type = '<f4' if encoding == 'float32weight_uint32joint' else '<u4'
    weights = z['bwgt_raw'].view(weight_type)[:n * 12].reshape(n, 12)
    return (*canonical_skin(ids, weights, encoding), encoding)


def captured_skin(vertex_view, weight_view, pipeline_uid):
    assert vertex_view['stride'] == 8
    n = vertex_view['num_elements']
    vertex_offset = vertex_view['first_element'] * vertex_view['stride']
    maps = np.frombuffer(read_resource(vertex_view['resource_uid'], vertex_offset, n * 8), '<u4').reshape(n, 2)
    if int(maps[:, 0].max(initial=0)) > 12:
        raise ValueError(('unexpected influence count', int(maps[:, 0].max())))
    # ByteAddress SRVs use R32_TYPELESS, whose firstElement unit is four bytes.
    assert weight_view['format'] == 39 and weight_view['flags'] == 1
    weight_offset = weight_view['first_element'] * 4
    weight_size = weight_view['num_elements'] * 4
    raw = read_resource(weight_view['resource_uid'], weight_offset, weight_size)
    encoding = 'float32weight_uint32joint' if pipeline_uid == 7931 else 'packed22weight10joint'
    record_size = 8 if pipeline_uid == 7931 else 4
    ids = np.zeros((n, 12), dtype='<u4')
    weights = np.zeros((n, 12), dtype='<f4' if record_size == 8 else '<u4')
    for i, (number, offset) in enumerate(maps):
        number, offset = int(number), int(offset)
        if offset + number * record_size > len(raw):
            raise ValueError(('weight bounds', i, offset, number, len(raw)))
        if number:
            if record_size == 8:
                pair = np.frombuffer(raw, dtype=np.dtype([('w', '<f4'), ('i', '<u4')]), count=number, offset=offset)
                ids[i, :number] = pair['i']
                weights[i, :number] = pair['w']
            else:
                packed = np.frombuffer(raw, dtype='<u4', count=number, offset=offset)
                ids[i, :number] = packed >> 22
                weights[i, :number] = packed & 4194303
    digest, nonzero = canonical_skin(ids, weights, encoding)
    return {'vertices': n, 'skin_sha256': digest, 'nonzero_influence_records': nonzero,
            'vertex_map_resource_uid': vertex_view['resource_uid'], 'vertex_map_resource_offset': vertex_offset,
            'vertex_map_bytes': n * 8, 'weight_resource_uid': weight_view['resource_uid'],
            'weight_resource_offset': weight_offset, 'weight_view_bytes': weight_size,
            'max_influences': int(maps[:, 0].max(initial=0)), 'weight_encoding': encoding}


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    raw_index = {}
    for path in list((EXPORT / 'ExactDebug').glob('*/capture.json')) + list((EXPORT / 'BackpackVariantDebug').glob('*/capture.json')):
        doc = json.loads(path.read_text())
        pak = Path(doc.get('pak', '')).name
        for mesh in doc.get('meshes', []):
            raw_index[pak, mesh['name']] = (path.parent, mesh)
    audit_path = EXPORT / 'owned_rig_integration_report.json'
    audit = json.loads(audit_path.read_text())['mesh_skin_audit']
    selected = []
    for item in audit:
        if item['source_pak'] in ('backpack-ellie.pak', 'ellie16-backpack.pak', 'ellie-backpack.pak'):
            continue
        submesh = item['mesh'].removeprefix('SM_')
        found = raw_index.get((item['source_pak'], submesh))
        if found is None:
            # Blender object IDs can truncate the original source submesh name.
            alternatives = [(folder, raw) for (pak, name), (folder, raw) in raw_index.items()
                            if pak == item['source_pak'] and raw['vertex_count'] == item['vertices']]
            if len(alternatives) != 1:
                raise ValueError(('ambiguous truncated source name', item, len(alternatives)))
            found = alternatives[0]
        folder, mesh = found
        selected.append((item['source_pak'], folder, mesh))
    selected.extend((pak, folder, mesh) for (pak, name), (folder, mesh) in raw_index.items() if pak == 'ellie-backpack.pak')
    assert len(selected) == 31, len(selected)
    binding = json.loads((CAP / 'deformer_descriptor_bindings_probe.json').read_text())
    dispatches = []
    seen = {}
    errors = []
    for command in binding['dispatches']:
        if command['pipeline_uid'] not in (7931, 7932, 7939):
            continue
        slots = command.get('tables', {}).get('3', {}).get('slots', [])
        if len(slots) < 3 or any(s is None for s in slots[:3]):
            errors.append({'sequence': command['sequence'], 'command': command['command_index'], 'error': 'unresolved root3 slots'})
            continue
        cbv, vertex_view, weight_view = slots[:3]
        try:
            key = (vertex_view['resource_uid'], vertex_view['first_element'], vertex_view.get('stride'),
                   weight_view['resource_uid'], weight_view['first_element'], weight_view.get('num_elements'), command['pipeline_uid'])
            if key not in seen:
                seen[key] = captured_skin(vertex_view, weight_view, command['pipeline_uid'])
            decoded = seen[key]
        except Exception as exc:
            errors.append({'sequence': command['sequence'], 'command': command['command_index'], 'error': str(exc)})
            continue
        dispatches.append({**decoded, 'sequence': command['sequence'], 'command_index': command['command_index'],
                           'commandlist_uid': command['commandlist_uid'], 'pipeline_uid': command['pipeline_uid'],
                           'dispatch_xyz': command['dispatch_xyz'], 'deformer_cbv_gpu_address': cbv['address'],
                           'deformer_cbv_size': cbv['size']})
    candidates = json.loads((CAP / 'skin_vsharp_candidates.json').read_text())['rows']
    rows = []
    for pak, folder, mesh in sorted(selected, key=lambda s: (s[0], s[2]['name'])):
        digest, nonzero, encoding = source_skin(folder, mesh)
        exact = [d for d in dispatches if d['vertices'] == mesh['vertex_count'] and d['skin_sha256'] == digest]
        count_only = [d for d in dispatches if d['vertices'] == mesh['vertex_count']]
        vsharp = [r for r in candidates if r['source_vertex_count'] == mesh['vertex_count']]
        palette = [r for r in vsharp if r['matrix_count'] == 1074 and r['palette_resource_offset'] == 125371136]
        garment = [r for r in vsharp if r['matrix_count'] == 78]
        examples = palette[:3] if palette else garment[:3]
        rows.append({'source_pak': pak, 'source_submesh': mesh['name'], 'source_material': mesh['material'],
                     'vertices': mesh['vertex_count'], 'source_skin_sha256': digest,
                     'source_nonzero_influence_records': nonzero, 'source_weight_encoding': encoding, 'actual_dispatch_exact_matches': exact,
                     'actual_dispatch_vertex_count_matches': len(count_only),
                     'historical_vsharp_candidates': len(vsharp), 'historical_exact_human_palette_candidates': len(palette),
                     'historical_hoodie78_palette_candidates': len(garment),
                     'historical_vsharp_examples': [{k: r[k] for k in ('cbv_resource_offset', 'matrix_count', 'palette_resource_offset', 'second_palette_resource_offset')} for r in examples],
                     'verification': 'actual_dispatch_original_ordered_skin_records_bit_exact' if exact else
                                     'vertex_count_only_not_exactly_associated'})
    result = {'selected_meshes': len(rows), 'selected_vertices': sum(r['vertices'] for r in rows),
              'bit_exact_actual_dispatch_meshes': sum(bool(r['actual_dispatch_exact_matches']) for r in rows),
              'captured_skin_dispatches': len(dispatches), 'unique_captured_skin_binding_pairs': len(seen),
              'dispatch_decode_errors': errors,
              'method': 'Captured CommandRecording root3 SRV slots supply vertex influence counts/byte offsets. Pipeline7931 uses8byte float32weight+uint32joint records;7932/7939 use4byte packed22bitweight+10bitjoint records. Original NPZ source arrays are compared without normalization; only zero-weight padding is omitted. SHA256 covers per-vertex nonzero counts and original ordered record bytes.',
              'scope': 'Actual dispatch records prove bound source skin data for this frame. Historical VSharp matches are separate initial-upload observations; their CBV payloads are not asserted to be the current dispatch CBV contents. Vertex counts alone do not identify assets when counts collide.',
              'source_selection_audit': str(audit_path), 'rows': rows}
    json_path = REPORT / 'CAPTURE_MESH_SOURCE_BINDING_VALIDATION.json'
    json_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Original mesh source association from captured GPU bindings', '',
             f"Selected: {len(rows)} subsets, {result['selected_vertices']:,} vertices.",
             f"Bit-exact source skin records in actual frame dispatches: {result['bit_exact_actual_dispatch_meshes']}/{len(rows)} subsets.", '',
             result['method'], '', result['scope'], '',
             '| Package | Subset | Vertices | Exact actual dispatches | Historical human-palette matches |',
             '|---|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['source_pak']} | {r['source_submesh']} | {r['vertices']} | {len(r['actual_dispatch_exact_matches'])} | {r['historical_exact_human_palette_candidates']} |")
    lines.extend(['', 'Detailed JSON includes actual sequence/command IDs, CBV GPU addresses, source resource offsets and hashes.',
                  'Human skin palette: UID7556 offset125371136. Hoodie75 valid matrices: UID7556 offset136907840; historical VSharp capacity78 and actual per-mesh skin record identity are recorded separately.'])
    (REPORT / 'CAPTURE_MESH_SOURCE_BINDING_VALIDATION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    print('UNMATCHED', [(r['source_pak'], r['source_submesh'], r['vertices']) for r in rows if not r['actual_dispatch_exact_matches']])


if __name__ == '__main__':
    main()
