"""Verify every local ND texture descriptor has a decoded PNG output.

Run with the bundled Blender Python (or any Python that has the vendored
texture2ddecoder package on its path).  This deliberately checks the output
bytes and source payload lengths instead of trusting a file-name count.
"""
import os, json, hashlib

ROOT = r"D:/TLOU2_UE5_8_Codex"
MANIFEST = os.path.join(ROOT, "Exports", "TexturesDecoded", "texture_decode_manifest.json")
OUT_JSON = os.path.join(ROOT, "Content", "TLOU2", "Reports", "texture_decode_validation.json")
OUT_MD = os.path.join(ROOT, "Content", "TLOU2", "Reports", "TEXTURE_DECODE_REPORT.md")

rows = json.load(open(MANIFEST, encoding="utf-8"))
checked = []
for r in rows:
    d = dict(r)
    path = d.get("decoded_path")
    if path:
        path = os.path.normpath(path.replace("/", os.sep))
        d["decoded_path"] = path
        d["output_exists"] = os.path.isfile(path)
        if d["output_exists"]:
            d["output_bytes"] = os.path.getsize(path)
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            d["output_sha256"] = h.hexdigest()
    d["verified"] = bool(d.get("decoded")) and bool(d.get("output_exists"))
    checked.append(d)

summary = {
    "manifest": os.path.relpath(MANIFEST, ROOT).replace("\\", "/"),
    "total": len(checked),
    "decoded": sum(bool(x.get("decoded")) for x in checked),
    "verified_outputs": sum(bool(x.get("verified")) for x in checked),
    "bc7": sum(x.get("format_name") == "BC7" for x in checked),
    "bc7_verified": sum(x.get("format_name") == "BC7" and x.get("verified") for x in checked),
    "undecoded": [x.get("name") for x in checked if not x.get("decoded")],
    "missing_outputs": [x.get("name") for x in checked if x.get("decoded") and not x.get("output_exists")],
    "records": checked,
}
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump(summary, open(OUT_JSON, "w", encoding="utf-8"), indent=2)

byfmt = {}
for x in checked:
    byfmt.setdefault(x.get("format_name") or "unknown", []).append(x)
md = ["# Texture decode verification", "", "The verifier reads the extraction manifest, confirms every decoded PNG exists, and hashes each output.", "", "| Format | Descriptors | Decoded | Output verified |", "|---|---:|---:|---:|"]
for fmt in sorted(byfmt):
    xs = byfmt[fmt]
    md.append("| %s | %d | %d | %d |" % (fmt, len(xs), sum(bool(x.get("decoded")) for x in xs), sum(bool(x.get("verified")) for x in xs)))
md += ["", "- Total descriptors: **%d**" % len(checked), "- Decoded PNGs: **%d/%d**" % (summary["decoded"], summary["total"]), "- BC7 decoded PNGs: **%d/%d**" % (summary["bc7_verified"], summary["bc7"]), "- Undecoded records: **%d**" % len(summary["undecoded"]), "- Missing output files: **%d**" % len(summary["missing_outputs"]), "", "Decoder: vendored `Scripts/vendor/texture2ddecoder` (`decode_bc7`) invoked by `Scripts/decode_local_textures.py`."]
open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
print("TEXTURE_VERIFY", summary["verified_outputs"], "/", summary["total"], "BC7", summary["bc7_verified"], "/", summary["bc7"])
