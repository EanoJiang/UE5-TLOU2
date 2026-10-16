"""Decode TLOU2 PC high-resolution textures with D3D12 block-row pitch.

Actor PAKs contain low-resolution resident mips.  Matching hash descriptors in
texturedict3 supply the complete higher-resolution images.  PC upload footprints
align each block row to 256 bytes; interpreting that padding as blocks produces
the horizontal stripe artifacts seen in the original catalog preview.
"""
import hashlib
import json
import struct
import zlib
import binascii
import sys
from pathlib import Path
import numpy as np

ROOT = Path("D:/TLOU2_UE5_8_Codex")
OUT = ROOT / "Exports/TexturesDecoded"
sys.path.insert(0, str(ROOT / "Scripts/vendor"))
import texture2ddecoder as texdec

FMT = {61: "R8", 71: "BC1", 72: "BC1", 77: "BC3", 78: "BC3", 80: "BC4", 83: "BC5", 98: "BC7", 99: "BC7"}

def png(path, w, h, rgba):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", binascii.crc32(t + d) & 0xffffffff)
    scan = b"".join(b"\0" + rgba[y*w*4:(y+1)*w*4] for y in range(h))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(scan, 6)) + chunk(b"IEND", b""))

manifest_path = OUT / "texture_decode_manifest.json"
resident = json.loads(manifest_path.read_text(encoding="utf-8"))
backup = OUT / "texture_decode_manifest_resident_before_pitch_fix.json"
if not backup.exists(): backup.write_text(json.dumps(resident, indent=2), encoding="utf-8")
dictionary = json.loads((OUT / "pc_texture_dictionary_index.json").read_text(encoding="utf-8"))
by_hash = {}
for row in dictionary:
    old = by_hash.get(row["hash"])
    if not old or row["width"] * row["height"] > old["width"] * old["height"]:
        by_hash[row["hash"]] = row

records = []
for old in resident:
    rec = dict(old)
    hi = by_hash.get(old["hash"])
    if not hi: raise RuntimeError("missing high-resolution hash " + str(old["hash"]))
    rec["resident_descriptor"] = {k: old.get(k) for k in ("source_pak", "descriptor_offset", "payload_abs", "size", "width", "height", "mips", "format")}
    rec["dictionary_descriptor"] = hi
    w, h, fmt = hi["width"], hi["height"], FMT[hi["format"]]
    block_size = 8 if fmt in ("BC1", "BC4") else 16
    row_bytes = w if fmt == 'R8' else ((w + 3) // 4) * block_size
    pitch = (row_bytes + 255) & ~255
    block_rows = h if fmt == 'R8' else (h + 3) // 4
    with open(hi["source_pak"], "rb") as fp:
        fp.seek(hi["payload_abs"])
        padded = fp.read(pitch * block_rows)
    if len(padded) != pitch * block_rows: raise RuntimeError("short texture payload " + old["name"])
    tight = b"".join(padded[y*pitch:y*pitch+row_bytes] for y in range(block_rows))
    if fmt == 'R8':
        gray = np.frombuffer(tight, dtype=np.uint8).reshape(h, w)
        rgba = np.empty((h,w,4), dtype=np.uint8)
        rgba[:,:,:3] = gray[:,:,None]
        rgba[:,:,3] = 255
    else:
        decode = getattr(texdec, "decode_" + fmt.lower())
        bgra = decode(tight, w, h)
        rgba = np.frombuffer(bgra, dtype=np.uint8).reshape(h, w, 4)[:, :, [2, 1, 0, 3]].copy()
    if fmt == "BC4":
        rgba[:, :, 1] = rgba[:, :, 0]
        rgba[:, :, 2] = rgba[:, :, 0]
    if fmt == "BC5":
        # BC5 stores normal X/Y. Reconstruct Z for Blender and uncompressed PNG
        # consumers; Unreal's normal compressor retains the same X/Y channels.
        xy = rgba[:, :, :2].astype(np.float32) / 127.5 - 1.0
        z = np.sqrt(np.maximum(0.0, 1.0 - (xy*xy).sum(axis=2)))
        rgba[:, :, 2] = np.rint((z + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
    out = OUT / (Path(old["name"]).stem + ".png")
    png(out, w, h, rgba.tobytes())
    rec.update({"width": w, "height": h, "mips": hi["mips"], "format": hi["format"], "format_name": fmt,
                "payload_bytes": hi["size"], "decoded_path": str(out), "decoded": True,
                "decode_source": "PC texturedict3 hash match", "block_row_bytes": row_bytes,
                "block_row_pitch": pitch, "top_mip_padded_bytes": len(padded),
                "top_mip_tight_bytes": len(tight), "decoder_channel_order": "BGRA converted to RGBA",
                "top_mip_sha256": hashlib.sha256(tight).hexdigest(), "png_sha256": hashlib.sha256(out.read_bytes()).hexdigest()})
    records.append(rec)
    print(old["name"], fmt, f"{w}x{h}", "pitch", pitch)
manifest_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
print("PC_HIGHRES_TEXTURES_DECODED", len(records))
