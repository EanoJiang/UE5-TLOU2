"""Audit output-offset tables in target codec without guessing bone identity.

Offsets are byte-aligned transform destinations, not proven source bit offsets.
The evidence is their modulo-48 pattern and count*48 sentinel in two groups.
"""
import json, struct, hashlib, collections
from pathlib import Path

ROOT = Path(r'D:/TLOU2_UE5_8_Codex')
PAK = Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
OUT = ROOT / 'Content/TLOU2/Reports'
START = 0x95ae20
SIZE = 0x9c0
SPEC = [('A_vector', 0x160, 16, 127), ('A_const_rotation', 0x1e0, 8, 127),
        ('A_dynamic_rotation', 0x290, 8, 127), ('B_vector', 0x2d0, 40, 38),
        ('B_rotation', 0x410, 24, 38)]

def main():
    blob = PAK.read_bytes()[START:START + SIZE]
    tables = []
    for name, off, n, count in SPEC:
        vals = struct.unpack_from('<' + str(n) + 'H', blob, off)
        sentinel = count * 48
        rows = [{'index': i, 'value': v, 'hex': f'0x{v:x}',
                 'record_index_if_48_bytes': v // 48,
                 'component_byte_if_48_bytes': v % 48,
                 'is_count_x_48_sentinel': v == sentinel} for i, v in enumerate(vals)]
        active = [r for r in rows if not r['is_count_x_48_sentinel']]
        tables.append({'name': name, 'offset': f'0x{off:x}', 'entries': n,
                       'section_record_count_candidate': count,
                       'sentinel': f'0x{sentinel:x}', 'sentinel_count': n-len(active),
                       'active_modulo_48': dict(collections.Counter(r['component_byte_if_48_bytes'] for r in active)),
                       'rows': rows})
    result = {'tool': 'probe_codec_destination_tables.py',
              'source': str(PAK), 'codec_offset': START,
              'payload_sha256': hashlib.sha256(blob).hexdigest(),
              'status': 'verified_arithmetic_pattern_destination_table_interpretation',
              'tables': tables,
              'observations': [
                  'All active offsets are congruent to 0, 16, or 32 modulo 48.',
                  'A_vector uses records 32,34,36,38,40,42,44 at components 0 and 32.',
                  'A_const_rotation uses records 40,42,44 at component 16; A_dynamic_rotation uses 32,34,38,36 at component 16.',
                  'B_vector uses odd records 1..37 at components 0 and 32; B_rotation uses the same odd records at component 16.',
                  'The padding values are exactly 127*48 (A) and 38*48 (B). These match the relevant high16 section words 0x007f and 0x0026.',
                  'The interleaving and sentinel pattern support destination transform offsets. Treating these values as source bit offsets into +0x500 is not supported.',
                  'The 48-byte record interpretation identifies three 16-byte component slots but does not by itself map a local section record index to a skeleton bone.',
              ],
              'unresolved': ['bone identity for section-local record indices', 'component slot transform conventions',
                             'compressed dynamic stream bit layout and interpolation', 'units and basis']}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'CODEC_41430102_DESTINATION_TABLES.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines = ['# 0x41430102 destination-offset table evidence', '',
             'The A/B/C tables previously used as source bit offsets have a stronger, exact arithmetic pattern: active values identify 48-byte records with component positions 0, 16, and 32. Padding entries are section-count × 48.', '',
             '| Table | Payload offset | Entries | Active modulo 48 | Sentinel | Padding entries |',
             '|---|---:|---:|---|---:|---:|']
    for t in tables:
        lines.append(f"| `{t['name']}` | `{t['offset']}` | {t['entries']} | `{t['active_modulo_48']}` | `{t['sentinel']}` | {t['sentinel_count']} |")
    lines += ['', '## Evidence interpretation', '', *['- '+x for x in result['observations']], '',
              'The former q48 table probe is retained for audit only; its source-bit-offset interpretation is withdrawn. This finding supplies a destination layout for the codec decoder but does not yet produce original bone animation tracks.']
    (OUT/'CODEC_41430102_DESTINATION_TABLES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'tables':len(tables),'json':str(OUT/'CODEC_41430102_DESTINATION_TABLES.json')},indent=2))

if __name__ == '__main__':
    main()
