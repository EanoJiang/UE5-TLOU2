"""Split the exact outfit GLB files into editable JSON glTF + BIN sources."""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def split_glb(glb: Path, gltf: Path, bin_path: Path) -> None:
    b = glb.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", b, 0)
    if magic != b"glTF" or version != 2 or total != len(b):
        raise ValueError(f"invalid GLB: {glb}")
    off = 12
    doc = None
    blob = None
    while off + 8 <= len(b):
        n, typ = struct.unpack_from("<II", b, off)
        chunk = b[off + 8 : off + 8 + n]
        if typ == 0x4E4F534A:
            doc = json.loads(chunk.decode("utf-8").rstrip(" \x00"))
        elif typ == 0x4E4942:
            blob = chunk
        off += 8 + n
    if doc is None or blob is None:
        raise ValueError(f"missing GLB chunks: {glb}")
    doc.setdefault("asset", {})["generator"] = "TLOU2_UE5_8_Codex glTF split"
    buffers = doc.get("buffers", [])
    if not buffers:
        buffers = [{"byteLength": len(blob)}]
        doc["buffers"] = buffers
    buffers[0].pop("uri", None)
    buffers[0]["byteLength"] = len(blob)
    buffers[0]["uri"] = bin_path.name
    bin_path.write_bytes(blob)
    gltf.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    exports = ROOT / "Exports"
    jobs = [
        (exports / "Ellie_Patrol_Catalog_Exact.glb", exports / "Ellie_Patrol_Catalog_Exact.gltf", exports / "Ellie_Patrol_Catalog_Exact.bin"),
        (exports / "Ellie_Patrol_ExactBody.glb", exports / "Ellie_Patrol_ExactBody.gltf", exports / "Ellie_Patrol_ExactBody.bin"),
    ]
    for glb, gltf, bin_path in jobs:
        split_glb(glb, gltf, bin_path)
    print(json.dumps({"sources": [str(x[1]) for x in jobs], "binary": [str(x[2]) for x in jobs]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
