#!/usr/bin/env python3
"""Record executable evidence for OrbisAnim smallest-three quantizer scale.

The PC executable embeds four copies of the IEEE-754 value
sqrt(1/2)/16384 (0x383504f3), immediately beside the OrbisAnim constant tables.
This report records the bytes and hashes only; it does not claim a complete
codec implementation.
"""
from __future__ import annotations
import hashlib, json, struct
from pathlib import Path

ROOT = Path(r"D:/TLOU2_UE5_8_Codex")
GAME = Path(r"D:/Steam/steamapps/common/The Last of Us Part II")
OUT = ROOT / "Content/TLOU2/Reports"
TARGET = 0x383504F3

def main() -> None:
    rows = []
    for name, off in (("tlou-ii.exe", 0x3005080), ("tlou-ii-l.exe", 0x303A2D0)):
        p = GAME / name
        b = p.read_bytes()
        sample = b[off : off + 16]
        rows.append({
            "executable": str(p),
            "sha256": hashlib.sha256(b).hexdigest(),
            "file_offset": hex(off),
            "sample_hex": sample.hex(),
            "repeat_count_4byte": len(sample) // 4,
            "u32": hex(struct.unpack_from("<I", sample)[0]),
            "float32": struct.unpack_from("<f", sample)[0],
            "expected_u32": hex(TARGET),
            "expected_float32": (2.0 ** -0.5) / 16384.0,
            "matches": struct.unpack_from("<I", sample)[0] == TARGET,
        })
    doc = {
        "tool": "report_orbisanim_quat_scale.py",
        "format_context": "OrbisAnim::ConstDecompressQuat48SmallestThree / DecompressQuatSmallestThree symbol strings are present in these executables.",
        "quantizer_evidence": "Four consecutive float32 constants equal sqrt(1/2)/16384 in each executable.",
        "rows": rows,
        "interpretation": "Supports the scale used by the storage-level 48-bit quaternion candidate probe; does not establish table-to-bone or temporal mapping.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ORBISANIM_QUAT_SCALE_EVIDENCE.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    md = ["# OrbisAnim 48-bit quaternion quantizer scale evidence", "", "The PC executables contain four consecutive copies of the float32 constant `sqrt(1/2)/16384` (`0x383504f3`) at the offsets below. Their embedded strings also name `OrbisAnim::ConstDecompressQuat48SmallestThree` and `OrbisAnim::DecompressQuatSmallestThree`.", "", "| executable | file offset | sample | decoded float | SHA-256 |", "|---|---:|---|---:|---|"]
    for r in rows:
        md.append(f"| `{Path(r['executable']).name}` | `{r['file_offset']}` | `{r['sample_hex']}` | `{r['float32']:.12g}` | `{r['sha256']}` |")
    md += ["", "This is executable format evidence for the scale used in `CODEC_41430102_QUAT48_CANDIDATES`. It does not prove descriptor-to-bone assignment, frame ordering, root motion, or a UE-valid animation."]
    (OUT / "ORBISANIM_QUAT_SCALE_EVIDENCE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(OUT / "ORBISANIM_QUAT_SCALE_EVIDENCE.json"), "md": str(OUT / "ORBISANIM_QUAT_SCALE_EVIDENCE.md")}, indent=2))

if __name__ == "__main__":
    main()
