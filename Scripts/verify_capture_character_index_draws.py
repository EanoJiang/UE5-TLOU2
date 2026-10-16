"""Close the character topology proof using actual captured IA index bytes."""
from pathlib import Path
import collections
import hashlib
import json
import struct
import numpy as np
from ngfx_resource_reader import object_blob, resource_pages, read_resource

ROOT = Path('D:/TLOU2_UE5_8_Codex')
CAP = ROOT / 'Exports/CaptureBuffers'
REPORT = ROOT / 'Content/TLOU2/Reports'


def main():
    selection = json.loads((REPORT / 'CAPTURE_MESH_SOURCE_BINDING_VALIDATION.json').read_text())
    raw_index = {}
    for path in list((ROOT / 'Exports/ExactDebug').glob('*/capture.json')) + list((ROOT / 'Exports/BackpackVariantDebug').glob('*/capture.json')):
        doc = json.loads(path.read_text())
        for mesh in doc.get('meshes', []):
            raw_index[Path(doc.get('pak', '')).name, mesh['name']] = path.parent, mesh
    source = collections.defaultdict(list)
    rows = []
    for selected in selection['rows']:
        if not selected['actual_dispatch_exact_matches']:
            continue
        folder, mesh = raw_index[selected['source_pak'], selected['source_submesh']]
        data = np.load(folder / mesh['npz'])['indices_raw'].tobytes()
        digest = hashlib.sha256(data).hexdigest()
        row = {'source_pak': selected['source_pak'], 'source_submesh': mesh['name'],
               'vertices': mesh['vertex_count'], 'indices': mesh['count'],
               'triangles': mesh['count'] // 3, 'source_index_bytes': len(data),
               'source_index_sha256': digest, 'source_skin_sha256': selected['source_skin_sha256'],
               'actual_index_draw_matches': []}
        rows.append(row)
        source[digest].append(row)
    assert len(rows) == 29, len(rows)
    allocations = []
    for uid in (5331, 5333, 5335, 5367):
        base = struct.unpack_from('<Q', object_blob(uid, 'create'), 104)[0]
        length = sum(p['bytes'] for p in resource_pages(uid))
        allocations.append((uid, base, length))
    cache = {}
    draws = json.loads((CAP / 'graphics_descriptor_bindings_probe.json').read_text())['dispatches']
    for draw in draws:
        ib = draw.get('index_buffer')
        if not ib or 'gpu_address' not in ib:
            continue
        count, instances, first, base_vertex, start_instance = draw['draw_args']
        if ib['format'] not in (57, 42):
            continue
        width = 2 if ib['format'] == 57 else 4
        address, size = ib['gpu_address'] + first * width, count * width
        key = address, size
        if key not in cache:
            allocation = next(((uid, base) for uid, base, length in allocations
                               if base <= address and address + size <= base + length), None)
            if allocation is None:
                cache[key] = None
                continue
            uid, base = allocation
            data = read_resource(uid, address - base, size)
            cache[key] = {'sha256': hashlib.sha256(data).hexdigest(), 'resource_uid': uid,
                          'resource_offset': address - base, 'bytes': size}
        recovered = cache[key]
        if recovered is None or recovered['sha256'] not in source:
            continue
        for row in source[recovered['sha256']]:
            if count != row['indices']:
                continue
            row['actual_index_draw_matches'].append({k: draw[k] for k in ('sequence', 'commandlist_uid', 'command_index', 'pipeline_uid', 'root_signature_uid', 'root_constants', 'draw_args')})
            row['actual_index_draw_matches'][-1]['index_buffer'] = recovered
    unmatched = [r['source_submesh'] for r in rows if not r['actual_index_draw_matches']]
    report = {'pass': not unmatched, 'character_subsets': len(rows),
              'vertices': sum(r['vertices'] for r in rows), 'triangles': sum(r['triangles'] for r in rows),
              'bit_exact_actual_indexed_draw_subsets': sum(bool(r['actual_index_draw_matches']) for r in rows),
              'actual_indexed_draw_matches': sum(len(r['actual_index_draw_matches']) for r in rows),
              'unmatched': unmatched,
              'method': 'SHA256 covers every original ordered u16 triangle index byte from source NPZ. Actual DrawIndexedInstanced IA views are resolved via captured resource GPU allocation bases; FirstIndexLocation and index width select the exact rendered byte range. Index count must also equal the original subset count. This supplements independent original ordered skin-record and captured shader point-position validation.',
              'rows': rows}
    path = REPORT / 'CAPTURE_CHARACTER_TRIANGLE_INDEX_VALIDATION.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['# Character triangle topology from actual captured DrawIndexed bindings', '',
             f"Bit-exact original triangle index bytes: {report['bit_exact_actual_indexed_draw_subsets']}/{len(rows)} subsets, {report['vertices']:,} vertices, {report['triangles']:,} triangles, {report['actual_indexed_draw_matches']} actual indexed-draw associations.", '',
             report['method'], '', '| Package | Subset | Triangles | Actual indexed-draw matches |', '|---|---|---:|---:|']
    lines.extend(f"| {r['source_pak']} | {r['source_submesh']} | {r['triangles']} | {len(r['actual_index_draw_matches'])} |" for r in rows)
    (REPORT / 'CAPTURE_CHARACTER_TRIANGLE_INDEX_VALIDATION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
    assert report['pass'], unmatched


if __name__ == '__main__':
    main()
