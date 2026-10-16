"""Strict reader for captured initial D3D12 CBV/SRV/UAV heaps.

The descriptor state encoding is a capture serialization, not a native D3D12
memory image. All supported records must consume the entire state blob.
"""
import struct
from ngfx_resource_reader import object_blob


def heap_addresses(uid):
    blob = object_blob(uid, 'create')
    increment, cpu, gpu = struct.unpack_from('<IQQ', blob, len(blob) - 21)
    if increment not in (8, 16, 32, 64):
        raise ValueError(('descriptor increment', uid, increment))
    return {'uid': uid, 'increment': increment, 'cpu': cpu, 'gpu': gpu}


def parse_heap(uid):
    blob = object_blob(uid)
    bitmap_size = struct.unpack_from('<Q', blob, 24)[0]
    pos = 32 + bitmap_size
    tag = struct.unpack_from('<I', blob, pos)[0]
    pos += 4
    if tag == 0xfa000004:
        count = 1
    elif tag == 0xfa000008:
        count = blob[pos]
        pos += 1
    elif tag == 0xfa000010:
        count = struct.unpack_from('<I', blob, pos)[0]
        pos += 4
    else:
        raise ValueError(('array tag', uid, pos, hex(tag)))
    entries = {}
    for slot in range(count):
        start = pos
        kind = struct.unpack_from('<I', blob, pos)[0]
        pos += 4
        if kind == 0:
            continue
        resource, reserved = struct.unpack_from('<QI', blob, pos)
        pos += 12
        item = {'kind': {1: 'CBV', 2: 'SRV', 3: 'UAV'}.get(kind, kind),
                'resource_uid': resource, 'state_offset': start,
                'slot': slot, 'reserved': reserved}
        if kind == 1:
            address, size = struct.unpack_from('<QI', blob, pos)
            pos += 12
            item.update(address=address, size=size)
        elif kind == 2:
            fmt, dimension, mapping = struct.unpack_from('<3I', blob, pos)
            size = {1: 32, 2: 24, 3: 32, 4: 28, 5: 36, 6: 16,
                    7: 20, 8: 24, 9: 24, 10: 32, 11: 20}.get(dimension)
            if size is None:
                raise ValueError(('SRV dimension', uid, slot, dimension))
            item.update(format=fmt, dimension=dimension, mapping=mapping)
            if dimension == 1:
                first, number, stride, flags = struct.unpack_from('<Q3I', blob, pos + 12)
                item.update(first_element=first, num_elements=number,
                            stride=stride, flags=flags)
            item['desc_hex'] = blob[pos:pos + size].hex()
            pos += size
        elif kind == 3:
            counter = struct.unpack_from('<Q', blob, pos)[0]
            pos += 8
            fmt, dimension = struct.unpack_from('<2I', blob, pos)
            size = {1: 36, 2: 12, 3: 20, 4: 16, 5: 24, 8: 20}.get(dimension)
            if size is None:
                raise ValueError(('UAV dimension', uid, slot, dimension))
            item.update(counter_uid=counter, format=fmt, dimension=dimension,
                        desc_hex=blob[pos:pos + size].hex())
            pos += size
        else:
            raise ValueError(('descriptor kind', uid, slot, kind))
        if pos > len(blob):
            raise ValueError(('descriptor bounds', uid, slot, pos, len(blob)))
        entries[slot] = item
    if pos != len(blob):
        raise ValueError(('descriptor trailing bytes', uid, pos, len(blob)))
    return {'uid': uid, 'slot_count': count, 'nonnull_count': len(entries),
            'decoded_bytes': pos, 'entries': entries}
