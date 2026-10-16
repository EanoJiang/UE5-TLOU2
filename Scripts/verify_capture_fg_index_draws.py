"""Match FG turntable original index bytes to actual indexed draws."""
from pathlib import Path
import collections
import hashlib
import json
import struct
import numpy as np
from ngfx_resource_reader import read_resource, object_blob, resource_pages

ROOT = Path('D:/TLOU2_UE5_8_Codex')
CAP = ROOT / 'Exports/CaptureBuffers'
RAW = ROOT / 'Exports/ExactDebug/keyart_turntable_fg'


def main():
    raw = json.loads((RAW / 'capture.json').read_text())
    source = collections.defaultdict(list)
    for mesh in raw['meshes']:
        digest = hashlib.sha256(np.load(RAW / mesh['npz'])['indices_raw'].tobytes()).hexdigest()
        source[digest].append(mesh)
    draws = json.loads((CAP / 'graphics_descriptor_bindings_probe.json').read_text())['dispatches']
    resources = []
    for uid in (5331, 5333, 5335):
        base = struct.unpack_from('<Q', object_blob(uid, 'create'), 104)[0]
        size = sum(p['bytes'] for p in resource_pages(uid))
        resources.append((uid, base, size))
    cache = {}
    matches = []
    for draw in draws:
        ib = draw.get('index_buffer')
        if not ib or 'gpu_address' not in ib:
            continue
        index_count, instances, first, base_vertex, start_instance = draw['draw_args']
        width = 2 if ib['format'] == 57 else 4
        address, size = ib['gpu_address'] + first * width, index_count * width
        key = address, size
        if key not in cache:
            allocation = next(((uid, base) for uid, base, length in resources
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
        for mesh in source[recovered['sha256']]:
            matches.append({**draw, 'source_name': mesh['name'], 'source_material': mesh['material'],
                            'vertices': mesh['vertex_count'], 'captured_index_buffer': recovered})
    coverage = collections.Counter(d['source_name'] for d in matches)
    assert len(coverage) == 33, len(coverage)
    instance_views = {}
    for draw in matches:
        slots = draw.get('tables', {}).get('4', {}).get('slots', [])
        if len(slots) < 2 or not slots[1] or slots[1].get('stride') != 192:
            continue
        view = slots[1]
        key = view['resource_uid'], view['first_element'] * 192, view['num_elements']
        instance_views.setdefault(key, []).append(draw)
    assert len(instance_views) == 1
    (uid, offset, number), actual = next(iter(instance_views.items()))
    matrices = np.frombuffer(read_resource(uid, offset, number * 192), '<f4').reshape(number, 3, 4, 4)
    report = {'actual_indexed_draw_matches': len(matches), 'source_subsets_with_exact_index_match': len(coverage),
              'index_match_draws_per_source_subset': dict(coverage), 'instance_resource_uid': uid,
              'instance_resource_offset': offset, 'instance_record_bytes': 192, 'instance_count': number,
              'instance_world_matrix_game': matrices[0, 0].tolist(),
              'instance_previous_world_matrix_game': matrices[0, 1].tolist(),
              'instance_third_matrix_game': matrices[0, 2].tolist(),
              'structured_instance_actual_indexed_draw_bindings': len(actual),
              'method': 'Exact SHA256 of original index arrays versus actual IA index-buffer views resolved through original captured GPU allocation bases. These associations supplement independently bit-exact original skin record matches. Root4 slot1 stride192 instance records contain three4x4 float32 matrices; vertex shader47400 consumes the first matrix as row-wise affine world transform.'}
    (CAP / 'fg_stage_index_draw_matches.json').write_text(json.dumps(matches, indent=2), encoding='utf-8')
    (ROOT / 'Content/TLOU2/Reports/CAPTURE_FG_STAGE_INDEX_INSTANCE_VALIDATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
