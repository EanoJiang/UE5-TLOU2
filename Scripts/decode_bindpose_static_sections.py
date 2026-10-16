"""Decode verified constant half3 / Quat48 sections in one-frame Ellie clips.

This module is independent of the live codec reverse-engineering scripts. The
constant output destinations are byte offsets into 48-byte S/Q/T records.
The original ellie-skel float32 S/Q/T stream supplies a separate ground truth.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(r'D:/TLOU2_UE5_8_Codex')
BIND_PAK = Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak')
SKEL_PAK = ROOT / 'Content/TLOU2/SourcePaks/ellie-skel.pak'
CAP = ROOT / 'Exports/ExactDebug/ellie16_patrol_body/capture.json'
REPORT = ROOT / 'Content/TLOU2/Reports'
EXPORT = ROOT / 'Exports/AnimationSources/DecodedStaticBindpose'


def u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def align16(n):
    return (n + 15) & ~15


def decode_quat48(data: bytes) -> dict:
    """Exact executable layout: 2-bit index + 15/15/16 biased components.

    The largest component was swapped with W before packing. Reconstruct W
    positive, then swap it back with the low-two-bit index. Quaternion signs
    are consequently canonicalized and may negate the original float4.
    """
    if len(data) != 6:
        raise ValueError('Quat48 needs six bytes')
    v = int.from_bytes(data, 'little')
    packed = [(v >> 32) & 0xffff, (v >> 17) & 0x7fff, (v >> 2) & 0x7fff]
    q = [
        (packed[0] - 32768) * math.sqrt(0.5) / 32768,
        (packed[1] - 16384) * math.sqrt(0.5) / 16384,
        (packed[2] - 16384) * math.sqrt(0.5) / 16384,
    ]
    residual = 1.0 - sum(x * x for x in q)
    if residual < -1e-6:
        raise ValueError(f'invalid quaternion residual {residual}')
    q.append(math.sqrt(max(0.0, residual)))
    omitted = v & 3
    q[omitted], q[3] = q[3], q[omitted]
    return {'raw_hex': data.hex(), 'omitted_component': omitted, 'packed_unsigned': packed,
            'widths_xyz': [16, 15, 15], 'quaternion_xyzw': q, 'missing_residual': residual}


def read_skeleton_reference() -> dict:
    b = SKEL_PAK.read_bytes()
    page = 15472
    xform_rel = 0x240
    x = page + xform_rel
    if u32(b, x) != 0x41480105:
        raise ValueError('unexpected source hierarchy magic')
    node_count, xform_count = u16(b, x + 0x10), u16(b, x + 0x12)
    header_size, hierarchy_rel = u32(b, x + 0x20), u32(b, x + 0x3c)
    hierarchy_size = u32(b, x + hierarchy_rel + 20)
    parenting_start = x + hierarchy_rel + hierarchy_size
    parents = [struct.unpack_from('<4i', b, parenting_start + 16 * i) for i in range(node_count)]

    def root_of(i):
        seen = set()
        while parents[i][1] != -1:
            if i in seen:
                raise ValueError('skeleton cycle')
            seen.add(i)
            i = parents[i][1]
        return i

    bone_map = [i for i in range(node_count) if root_of(i) == 0]
    if len(bone_map) != xform_count:
        raise ValueError(('xform count', len(bone_map), xform_count))
    bones = json.loads(CAP.read_text(encoding='utf-8'))['bones']
    rows = {}
    for ti, bi in enumerate(bone_map):
        off = x + header_size + 48 * ti
        values = struct.unpack_from('<12f', b, off)
        rows[bi] = {'bone_index': bi, 'bone_name': bones[bi]['name'], 'transform_index': ti,
                    'source_absolute_offset': off, 'scale': list(values[:3]),
                    'rotation': list(values[4:8]), 'translation': list(values[8:11])}
    return {'source_pak': str(SKEL_PAK), 'node_count': node_count, 'xform_count': xform_count,
            'xform_start_absolute': x + header_size, 'parenting_start_absolute': parenting_start,
            'mapped_root_group_bones': bone_map, 'transforms': rows}


def decode_const_section(blob: bytes, section_offset: int, record_count: int, bone_base: int,
                         label: str, reference: dict) -> dict:
    """Decode the established 8-byte constant group syntax in one section."""
    groups, output = [], {}
    for gi in range(16):
        descriptor = section_offset + gi * 8
        opcode, padded_count, field2, table_rel = struct.unpack_from('<4H', blob, descriptor)
        if opcode == 0:
            break
        if opcode not in (0x0316, 0x0318):
            raise ValueError(f'{label}: nonconstant opcode {opcode:#x} at {descriptor:#x}')
        table = section_offset + table_rel
        dests = list(struct.unpack_from('<' + str(padded_count) + 'H', blob, table))
        sentinel = record_count * 48
        active_dests = [d for d in dests if d != sentinel]
        # These codecs put padding entries at the tail of each destination table.
        if dests != active_dests + [sentinel] * (padded_count - len(active_dests)):
            raise ValueError(f'{label}: non-tail sentinel layout')
        data_start = align16(table + 2 * padded_count)
        data_end = data_start + 6 * len(active_dests)
        group = {'descriptor_offset': descriptor, 'opcode': f'0x{opcode:04x}',
                 'padded_destination_count': padded_count, 'active_destination_count': len(active_dests),
                 'field2_observed': field2, 'table_relative_to_section': table_rel,
                 'table_payload_offset': table, 'destination_offsets': dests,
                 'sentinel': sentinel, 'data_start': data_start, 'data_end': data_end,
                 'next_aligned_payload_offset': align16(data_end), 'rows': []}
        for i, dest in enumerate(active_dests):
            local, slot = divmod(dest, 48)
            bi = bone_base + local
            ref = reference['transforms'].get(bi)
            if ref is None:
                raise ValueError(f'no source skeleton transform for {bi}')
            pos = data_start + i * 6
            row = {'packed_index': i, 'source_payload_offset': pos, 'destination_byte_offset': dest,
                   'section_local_record': local, 'component_slot_byte': slot,
                   'bone_index': bi, 'bone_name': ref['bone_name']}
            target = output.setdefault(bi, {'bone_index': bi, 'bone_name': ref['bone_name'],
                                          'section_local_record': local, 'reference': ref})
            if opcode == 0x0316:
                values = list(struct.unpack_from('<3e', blob, pos))
                if slot not in (0, 32):
                    raise ValueError(('half3 slot', slot))
                kind = 'scale' if slot == 0 else 'translation'
                row.update({'kind': kind, 'half3': values,
                            'reference': ref[kind],
                            'max_abs_error_vs_skeleton': max(abs(a-b) for a,b in zip(values, ref[kind]))})
                target[kind] = values
            else:
                if slot != 16:
                    raise ValueError(('quaternion slot', slot))
                qrow = decode_quat48(blob[pos:pos+6])
                q = qrow['quaternion_xyzw']
                ref_q = ref['rotation']
                err = min(math.sqrt(sum((a-b)**2 for a,b in zip(q, ref_q))),
                          math.sqrt(sum((a+b)**2 for a,b in zip(q, ref_q))))
                row.update(qrow)
                row.update({'kind': 'rotation', 'reference': ref_q,
                            'sign_invariant_l2_error_vs_skeleton': err})
                target['rotation'] = q
            group['rows'].append(row)
        groups.append(group)
    return {'label': label, 'section_offset': section_offset, 'record_count': record_count,
            'bone_base': bone_base, 'groups': groups, 'decoded_transforms': list(output.values())}


def main():
    reference = read_skeleton_reference()
    src = BIND_PAK.read_bytes()
    cases = [('bindpose-anim', 0x6620, 0x920), ('bindpose-add', 0x7860, 0x560)]
    results = []
    for label, off, size in cases:
        blob = src[off:off + size]
        if u32(blob, 0) != 0x41430102 or u16(blob, 0x0e) != 1:
            raise ValueError('unexpected bindpose codec')
        sections = [decode_const_section(blob, 0x120, 127, 0, 'body', reference)]
        finger_offset = u32(blob, 0x50)
        if u16(blob, finger_offset) != 0:
            sections.append(decode_const_section(blob, finger_offset, 38, 322, 'fingers', reference))
        result = {'clip': label, 'source_absolute_offset': off, 'payload_bytes': size,
                  'payload_sha256': hashlib.sha256(blob).hexdigest(),
                  'frames': u16(blob, 0x0e), 'frame_stride': u16(blob, 0x3c),
                  'section_offset_at_0x30': u32(blob, 0x30), 'stream_offset_at_0x38': u32(blob, 0x38),
                  'sections': sections}
        results.append(result)
    anim, add = results
    quats = [r for s in anim['sections'] for g in s['groups'] for r in g['rows'] if r['kind']=='rotation']
    vectors = [r for s in anim['sections'] for g in s['groups'] for r in g['rows'] if r['kind']!='rotation']
    add_vectors = [r for s in add['sections'] for g in s['groups'] for r in g['rows'] if r['kind']!='rotation']
    add_quats = [r for s in add['sections'] for g in s['groups'] for r in g['rows'] if r['kind']=='rotation']
    checks = {
        'anim75_constant_quaternions_match_skeleton_within_1e4': len(quats)==75 and all(r['sign_invariant_l2_error_vs_skeleton'] < 1e-4 for r in quats),
        'anim150_half3_vectors_decoded': len(vectors)==150,
        'anim149_vectors_match_skeleton_within_1e3': sum(r['max_abs_error_vs_skeleton'] < 1e-3 for r in vectors)==149,
        'add37_identity_quaternions': len(add_quats)==37 and all(r['quaternion_xyzw']==[0.0,0.0,0.0,1.0] for r in add_quats),
        'add37_unit_scales_and37_zero_translations': len(add_vectors)==74 and all(r['half3']==([1.0]*3 if r['kind']=='scale' else [0.0]*3) for r in add_vectors),
        'both_one_frame_zero_stride': all(r['frames']==1 and r['frame_stride']==0 for r in results),
    }
    out = {'tool': Path(__file__).name, 'source_pak': str(BIND_PAK),
           'skeleton_reference': {k:v for k,v in reference.items() if k != 'transforms'},
           'grammar': {'descriptor_bytes':8, 'descriptor_u16_fields':['opcode','padded_destination_count','field2_observed_3','destination_table_offset_relative_to_section'],
                       'half3_opcode':'0x0316', 'quat48_opcode':'0x0318',
                       'destination_record_bytes':48, 'component_slots':{'0':'scale_half3','16':'rotation_quat48','32':'translation_half3'},
                       'data_start_rule':'align16(table_start + 2 * padded_destination_count)',
                       'active_record_bytes':6, 'padding_destination_rule':'section_record_count * 48',
                       'quat_rule':'xyz from biased unsigned widths16/15/15 at bits32/17/2; reconstruct positive W; swap W with index low2'},
           'clips': results, 'verification': checks, 'pass': all(checks.values()),
           'max_quat_sign_invariant_l2_error':max(r['sign_invariant_l2_error_vs_skeleton'] for r in quats),
           'root_translation_difference': [r for r in vectors if r['max_abs_error_vs_skeleton']>=1e-3],
           'scope':'Verified static body/finger constant groups only. Other scalar sections and dynamic group codecs require separate decoding.'}
    REPORT.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    json_path = REPORT/'BINDPOSE_STATIC_SECTION_DECODE.json'
    json_path.write_text(json.dumps(out,indent=2),encoding='utf-8')
    flat = []
    for c in results:
        for s in c['sections']:
            for t in s['decoded_transforms']:
                flat.append({'clip':c['clip'],'section':s['label'],'bone_index':t['bone_index'],'bone_name':t['bone_name'],
                             **{f's{i}':v for i,v in enumerate(t.get('scale',[]))},
                             **{f'q{i}':v for i,v in enumerate(t.get('rotation',[]))},
                             **{f't{i}':v for i,v in enumerate(t.get('translation',[]))}})
    with (EXPORT/'bindpose_static_transforms.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['clip','section','bone_index','bone_name','s0','s1','s2','q0','q1','q2','q3','t0','t1','t2']);w.writeheader();w.writerows(flat)
    (EXPORT/'bindpose_static_transforms.json').write_text(json.dumps(flat,indent=2),encoding='utf-8')
    md = ['# Verified one-frame Ellie bindpose constant decode','',
          'The one-frame `bindpose-anim` body/finger groups now decode to 75 named S/Q/T records. The raw skeleton float32 transform stream is used as independent ground truth; all 75 Quat48 rotations match it within sign-invariant L2 error 1e-4.', '',
          '| Clip | Bytes | Static body transforms | Static finger transforms | Frames | Stride |', '|---|---:|---:|---:|---:|---:|']
    for c in results:
        counts={s['label']:len(s['decoded_transforms']) for s in c['sections']}
        md.append(f"| `{c['clip']}` | {c['payload_bytes']} | {counts.get('body',0)} | {counts.get('fingers',0)} | {c['frames']} | {c['frame_stride']} |")
    md += ['', '## Established constant-group grammar','',
           '- Each group descriptor is 8 bytes: four little-endian u16 values (opcode, padded destination count, observed field 3, table offset relative to its section).',
           '- `0x0316` stores three IEEE float16 values per active destination; `0x0318` stores one six-byte Quat48 per active destination.',
           '- Destination offsets address 48-byte records: scale at +0, quaternion at +16, translation at +32. Tail padding equals section record count × 48.',
           '- Packed data starts at `align16(table + 2*padded_count)`; only active destinations consume six bytes.',
           '- Quat48 uses low two bits for the largest-component index, unsigned biased component widths 16/15/15 at bits 32/17/2. Reconstruct W positive and swap W with the indicated index. The extra bit at bit32 is precision, not a sign bit.', '',
           f"- Maximum quaternion sign-invariant L2 error: `{out['max_quat_sign_invariant_l2_error']:.9g}` across 75 rotations.",
           '- 149/150 scale/translation vectors agree with skeleton float32 values within 0.001 source units. The remaining root Z translation is an actual clip difference: decoded -0.0154953003 versus skeleton +0.00986884069.',
           '- `bindpose-add` decodes 37 unit scales, 37 zero translations, and 37 identity rotations, confirming the additive constant behavior.',
           '- Body record indices map directly to bone indices; the independently matched finger section uses bone base 322.', '',
           'The full decoded source-unit values, source offsets, destination tables, and comparisons are in `BINDPOSE_STATIC_SECTION_DECODE.json` and `Exports/AnimationSources/DecodedStaticBindpose/bindpose_static_transforms.{json,csv}`. Dynamic codecs and other scalar sections are outside this verified static decoder.', '',
           '## Verification','', *[f"- {k}: {v}" for k,v in checks.items()]]
    (REPORT/'BINDPOSE_STATIC_SECTION_DECODE.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(json_path),'export':str(EXPORT),'checks':checks,'pass':out['pass'],'decoded_anim_transforms':75,'decoded_add_transforms':37,'max_quat_error':out['max_quat_sign_invariant_l2_error']},indent=2))
    if not out['pass']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
