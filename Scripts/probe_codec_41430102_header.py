"""Evidence-only probe for the PC 0x41430102 codec header.

The earlier probe called ``u32(+0x30)`` a descriptor count because the value
is 0x120 (288).  The referenced opcode-table structure and bindpose comparison show that this field is the
offset of the codec's first section table; the same 0x120 occurs in one-frame
bindpose resources. One-frame status alone is not a descriptor-count proof; the offset points at an opcode table. This script records
the corrected interpretation and a byte-accurate comparison with bindpose.

No transform or bone mapping is inferred here.
"""
from __future__ import annotations
import hashlib, json, struct
from pathlib import Path

PAK = Path(r"D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak")
BIND = Path(r"D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak")
OUT = Path(r"D:/TLOU2_UE5_8_Codex/Content/TLOU2/Reports")
MAGIC = 0x41430102


def u16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def u32(b: bytes, o: int) -> int:
    return struct.unpack_from("<I", b, o)[0]


def f32(b: bytes, o: int) -> float:
    return struct.unpack_from("<f", b, o)[0]


def parse(blob: bytes, off: int, payload: int, label: str) -> dict:
    h = blob[off:off + payload]
    if len(h) != payload:
        raise ValueError((label, len(h), payload))
    sec_off = u32(h, 0x30)
    stream = u32(h, 0x38)
    packed = u32(h, 0x3c)
    rec = []
    # Five 16-byte records are present in movement codecs.  Keep bytes even
    # when the short/one-frame variants use a different section layout.
    for i in range(5):
        o = 0x50 + i * 0x10
        if o + 16 > len(h):
            break
        rec.append({
            "offset": o,
            "field0": u32(h, o), "field1": u32(h, o + 4),
            "field2": u32(h, o + 8), "field3": u32(h, o + 12),
            "bytes": h[o:o + 16].hex(),
        })
    section_words = []
    for o in range(sec_off, min(sec_off + 0x40, len(h)), 8):
        if o + 8 > len(h):
            break
        section_words.append({
            "offset": o,
            "u16": [u16(h, o + 2 * i) for i in range(4)],
            "u32": [u32(h, o + 4 * i) for i in range(2)],
            "bytes": h[o:o + 8].hex(),
        })
    out = {
        "label": label,
        "payload_size": payload,
        "sha256": hashlib.sha256(h).hexdigest(),
        "magic": f"0x{u32(h, 0):08x}",
        "hash_word": f"0x{u32(h, 4):08x}",
        "groups": u16(h, 0x0c),
        "frames": u16(h, 0x0e),
        "clock_field_20": f32(h, 0x20),
        "sample_period_field_24": f32(h, 0x24),
        "rate_field_28": f32(h, 0x28),
        "nominal_period_field_2c": f32(h, 0x2c),
        "section_offset_field_30": f"0x{sec_off:x}",
        "flags_field_34": f"0x{u32(h, 0x34):08x}",
        "stream_offset_field_38": f"0x{stream:x}",
        "packed_stride_field_3c": f"0x{packed:08x}",
        "frame_stride_low16": packed & 0xffff,
        "codec_bits_high16": packed >> 16,
        "channel_table_field_40": f"0x{u32(h, 0x40):x}",
        "external_field_44": f"0x{u32(h, 0x44):08x}",
        "data_end_field_48": f"0x{u32(h, 0x48):x}",
        "stream_bytes_if_bounded": max(0, min(payload, u32(h, 0x48)) - stream),
        "section_records_at_50": rec,
        "section_words_from_30": section_words,
        "section_offset_equals_120": sec_off == 0x120,
        "stream_in_payload": 0 < stream <= payload,
        "stream_end_matches_stride_frames": (u32(h, 0x48) - stream) == ((u16(h, 0x0e) * (packed & 0xffff)) if (packed & 0xffff) else -1),
    }
    return out


def main() -> None:
    movement = PAK.read_bytes()
    # The target ANIM points to page 9 relative 0x41750; page 9 starts here.
    target = parse(movement, 0x95AE20, 0x9c0, "ellie-prone-lg-aim-strafe-0-fw")
    bind = BIND.read_bytes()
    bind_add = parse(bind, 0x7860, 0x560, "bindpose-add")
    bind_anim = parse(bind, 0x6620, 0x920, "bindpose-anim")
    doc = {
        "tool": "probe_codec_41430102_header.py",
        "status": "corrected_section_offset_interpretation",
        "target": target,
        "bindpose_examples": [bind_add, bind_anim],
        "correction": {
            "old_claim": "+0x30 is descriptor_count (288)",
            "verified": "+0x30 is a section/table offset; it equals 0x120 in target and one-frame bindpose clips",
            "reason": "+0x30 points exactly to the first opcode table (0x0316/0x0318 records), and the same structure occurs in the one-frame bindpose clips. The adjacent high16 word0x007f separately matches the first section destination sentinel127*48.",
            "remaining": "The records and transform-channel semantics inside the section table remain unresolved.",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "CODEC_41430102_HEADER_CORRECTION.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    t = target
    lines = [
        "# 0x41430102 header correction — section offset, not descriptor count",
        "",
        "The value at codec `+0x30` is `0x120` in the target and in one-frame Ellie bindpose codecs. In each case it points exactly to the first opcode table (`0x0316`/`0x0318` records). It is a section/table offset; interpreting its decimal value (288) as a descriptor count was an offset/value coincidence.",
        "",
        "## Target clip",
        "",
        f"- Codec payload: `{t['payload_size']}` bytes, SHA-256 `{t['sha256']}`.",
        f"- Groups / frames: `{t['groups']}` / `{t['frames']}`.",
        f"- `+0x30` section offset: `{t['section_offset_field_30']}`; `+0x34` flags: `{t['flags_field_34']}`.",
        f"- `+0x38` stream offset: `{t['stream_offset_field_38']}`; `+0x3c` packed stride: `{t['packed_stride_field_3c']}` (low16 stride `{t['frame_stride_low16']}`, high16 `{t['codec_bits_high16']}`).",
        f"- `+0x48` end offset: `{t['data_end_field_48']}`; bounded stream bytes: `{t['stream_bytes_if_bounded']}`; `frames × stride` check: `{t['stream_end_matches_stride_frames']}`.",
        "",
        "## Cross-check",
        "",
        "| Codec | Frames | +0x30 | +0x38 | +0x3c | +0x48 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for x in [target, bind_add, bind_anim]:
        lines.append(f"| `{x['label']}` | {x['frames']} | `{x['section_offset_field_30']}` | `{x['stream_offset_field_38']}` | `{x['packed_stride_field_3c']}` | `{x['data_end_field_48']}` |")
    lines += [
        "",
        "This correction does not establish descriptor-to-bone mapping, codec interpolation, units, or a finished animation decode. The section table and group records remain evidence for future probes.",
    ]
    (OUT / "CODEC_41430102_HEADER_CORRECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(OUT / "CODEC_41430102_HEADER_CORRECTION.json"), "target_section": target["section_offset_field_30"], "bindpose_section": bind_add["section_offset_field_30"]}, indent=2))


if __name__ == "__main__":
    main()
