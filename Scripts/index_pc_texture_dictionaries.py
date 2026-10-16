"""Index the high-resolution PC VRAM descriptors without loading payload PAKs."""
import json
import mmap
import struct
from pathlib import Path

ROOT = Path("D:/TLOU2_UE5_8_Codex")
DICT = Path("D:/Unpack_3A/TLOU2/Assets/tlou2_assets/texturedict3")
OUT = ROOT / "Exports/TexturesDecoded/pc_texture_dictionary_index.json"

def u16(b, p): return struct.unpack_from("<H", b, p)[0]
def u32(b, p): return struct.unpack_from("<I", b, p)[0]
def u64(b, p): return struct.unpack_from("<Q", b, p)[0]
def cstr(b, p):
    if not (0 <= p < len(b)): return ""
    return b[p:b.find(b"\0", p)].decode("utf-8", "replace")

rows = []
for path in sorted(DICT.glob("*.pak")):
    found = 0
    with path.open("rb") as fp, mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ) as b:
        pages = [struct.unpack_from("<3I", b, u32(b, 20) + i * 12) for i in range(u32(b, 16))]
        raw_start = pages[-1][0] + pages[-1][1]
        for pi, (po, ps, _) in enumerate(pages):
            for ei in range(u16(b, po + 18)):
                ent = po + 20 + ei * 16
                desc = po + u32(b, ent + 8)
                if cstr(b, po + u64(b, desc + 8)) != "VRAM_DESC": continue
                desc += 16  # TLOU2 adds 16 bytes before the VRAM descriptor body.
                h = u64(b, desc + 56)
                tex_path = cstr(b, desc + 112)
                rows.append({
                    "hash": h, "source_pak": str(path), "descriptor_offset": desc,
                    "page": pi, "entry": ei, "raw_start": raw_start,
                    "payload_offset": u32(b, desc + 40),
                    "payload_abs": raw_start + u32(b, desc + 40),
                    "size": u32(b, desc + 48), "format": u32(b, desc + 72),
                    "mips": u32(b, desc + 80), "width": u32(b, desc + 84),
                    "height": u32(b, desc + 88), "texture_path": tex_path,
                })
                found += 1
    print(path.name, found)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("INDEX", len(rows), OUT)
