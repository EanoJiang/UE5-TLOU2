"""Preserve a legacy 288-row joint-marker scan without asserting codec order.

The file names retain the earlier scan limit for provenance. The target header
word at +0x30 is the section/table offset 0x120, not a proven descriptor count.
Rows cross ANIM resource boundaries and are never assigned codec indices.
"""
import collections
import json
import struct
from pathlib import Path

ROOT = Path(r'D:/TLOU2_UE5_8_Codex')
PAK = Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
CAP = ROOT / 'Exports/ExactDebug/ellie16_patrol_body/capture.json'
REP = ROOT / 'Content/TLOU2/Reports'
SCAN_ROW_LIMIT = 288  # Historical arbitrary output cap; not codec metadata.


def fnv(s):
    h = 0xcbf29ce484222325
    for x in s.encode():
        h = ((h ^ x) * 0x100000001b3) & 0xffffffffffffffff
    return h


def main():
    b = PAK.read_bytes()
    page = 9541328
    rel = 0x8e150
    raw = b[page + rel:page + rel + 0x30000]
    d = json.loads(CAP.read_text())
    by = {fnv(x['name']): x for x in d['bones']}
    joint, nameh = fnv('joint'), fnv('name')
    allm = []
    for o in range(len(raw) - 16):
        if struct.unpack_from('<Q', raw, o)[0] == joint:
            if struct.unpack_from('<Q', raw, o + 8)[0] in by:
                allm.append(o)

    def cstr(o):
        e = b.find(b'\0', o)
        return b[o:e].decode('utf8', 'replace') if e >= 0 else ''

    _, pt = struct.unpack_from('<II', b, 16)
    po, _, _ = struct.unpack_from('<3I', b, pt + 12 * 9)
    starts = []
    for ei in range(struct.unpack_from('<H', b, po + 18)[0]):
        _, ro = struct.unpack_from('<QI', b, po + 20 + 16 * ei)
        rs = po + ro
        nameptr, typeptr = struct.unpack_from('<QQ', b, rs)
        starts.append((ro, ei, cstr(po + typeptr), cstr(po + nameptr)))
    starts.sort()

    rows, run_id, prev = [], -1, None
    for i, o in enumerate(allm[:SCAN_ROW_LIMIT]):
        if prev is None or o - prev != 48:
            run_id += 1
        rec = o - 8
        bh = struct.unpack_from('<Q', raw, o + 8)[0]
        bone = by[bh]
        q = [struct.unpack_from('<Q', raw, rec + 8 * j)[0] if 0 <= rec + 8 * j and rec + 8 * j + 8 <= len(raw) else None for j in range(7)]
        ro, ei, typ, name = [x for x in starts if x[0] <= rel + o][-1]
        rows.append({
            'scan_record_index': i, 'joint_run': run_id,
            'b_relative_marker_offset': o, 'page_relative_marker_offset': rel + o,
            'record_offset_b_relative': rec, 'bone_index': bone['index'],
            'bone_name': bone['name'], 'bone_hash': f'0x{bh:016x}',
            'record_plus40': f'0x{q[5]:016x}' if q[5] is not None else None,
            'record_qwords': [f'0x{x:016x}' if x is not None else None for x in q],
            'index_basis': 'scan enumeration only; not a codec descriptor index',
            'page9_resource_entry': ei, 'page9_resource_start_relative': hex(ro),
            'page9_resource_type': typ, 'page9_resource_name': name,
        })
        prev = o
    out = {
        'tool': 'build_lg_288_mapping.py', 'status': 'cross_resource_joint_marker_scan_not_codec_mapping',
        'legacy_filename_note': '288 is an arbitrary historical scan row limit, not a verified descriptor count.',
        'target_clip': 'ellie-prone-lg-aim-strafe-0-fw',
        'target_codec_payload_page_relative': '0x41750',
        'target_section_table_offset_at_plus_0x30': '0x120', 'descriptor_count_claim': None,
        'source_external_B_page_relative': '0x8e150', 'joint_marker_hash': f'0x{joint:016x}',
        'name_hash': f'0x{nameh:016x}', 'marker_count_scanned': len(allm),
        'scan_row_limit': SCAN_ROW_LIMIT, 'scan_record_count': len(rows),
        'unique_bones': sorted(set(r['bone_name'] for r in rows)),
        'bone_counts': dict(collections.Counter(r['bone_name'] for r in rows)),
        'run_count': run_id + 1, 'rows': rows,
        'page9_resource_entry_counts': dict(collections.Counter(str(r['page9_resource_entry']) for r in rows)),
        'verification_status': 'The scan crosses multiple ANIM resources. Row count and row order provide no proven correspondence to target codec transform channels.',
        'transform_channel_semantics_resolved': False,
    }
    REP.mkdir(parents=True, exist_ok=True)
    (REP / 'lg_target_288_descriptor_bone_candidates.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    md = [
        '# Legacy 288-row cross-resource joint-marker scan', '',
        '- Target header `+0x30` is the section/table offset `0x120`; it is not a verified descriptor count.',
        f'- Scanned from external B pointer page 9 relative `0x{rel:x}`; the first {SCAN_ROW_LIMIT} valid FNV(`joint`) records are preserved in source scan order.',
        f'- Valid joint markers scanned overall: `{len(allm)}`; retained rows: `{len(rows)}`; unique bones: `{len(out["unique_bones"])}`.',
        '- The retained rows cross multiple ANIM resource boundaries and do not belong to a proven primary-clip channel table.', '',
        'The legacy file names retain “288” for traceability. This number is an arbitrary scan cap inherited from the earlier mistaken header interpretation; it is not count-match evidence. Scan indices are not codec descriptor indices. Transform-channel, temporal ordering and bone mapping semantics remain unresolved.', '',
        '| Scan index | Run | Page-relative marker | Resource entry | Bone |', '|---:|---:|---:|---:|---|',
    ]
    for r in rows[:64]:
        md.append(f"| {r['scan_record_index']} | {r['joint_run']} | `0x{r['page_relative_marker_offset']:x}` | {r['page9_resource_entry']} | `{r['bone_name']}` |")
    md += ['', f'Only the first 64 scan rows are shown; all {len(rows)} rows and owning resource metadata are in `lg_target_288_descriptor_bone_candidates.json`.']
    (REP / 'LG_TARGET_288_DESCRIPTOR_BONE_CANDIDATES.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(REP / 'lg_target_288_descriptor_bone_candidates.json'), 'scan_rows': len(rows), 'runs': out['run_count'], 'resource_count': len(out['page9_resource_entry_counts']), 'descriptor_count_claim': None}, indent=2))


if __name__ == '__main__':
    main()
