"""Pure-Python handoff verification for the Ellie Patrol UE project.

This check intentionally does not reinterpret Naughty Dog animation bytes. It
checks the portable interchange files, decoded texture outputs, source package
presence, preview media, and the canonical UE commandlet report so the handoff
can be audited on a machine without Blender installed.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "Exports"
REPORTS = ROOT / "Content" / "TLOU2" / "Reports"
OUT_JSON = EXPORTS / "deliverable_verification_2026-10-16.json"
OUT_MD = REPORTS / "DELIVERABLE_VERIFICATION_2026-10-16.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_file(rel: str, kind: str, min_bytes: int = 1) -> dict[str, Any]:
    p = ROOT / rel
    ok = p.is_file() and p.stat().st_size >= min_bytes
    row: dict[str, Any] = {
        "path": rel.replace("\\", "/"),
        "kind": kind,
        "ok": ok,
        "bytes": p.stat().st_size if p.exists() else 0,
    }
    if ok:
        row["sha256"] = sha256(p)
    return row


def inspect_glb(rel: str) -> dict[str, Any]:
    p = ROOT / rel
    row = check_file(rel, "glb", 20)
    if not row["ok"]:
        return row
    try:
        b = p.read_bytes()
        magic, version, total = struct.unpack_from("<4sII", b, 0)
        row.update({"magic": magic.decode("ascii", "replace"), "version": version, "total_length": total})
        if magic != b"glTF" or version != 2:
            row["ok"] = False
            return row
        off = 12
        doc = None
        while off + 8 <= len(b):
            n, typ = struct.unpack_from("<II", b, off)
            chunk = b[off + 8 : off + 8 + n]
            if typ == 0x4E4F534A:
                doc = json.loads(chunk.decode("utf-8").rstrip(" \x00"))
                break
            off += 8 + n
        if doc is None:
            row["ok"] = False
            return row
        skins = doc.get("skins", [])
        joints = len(skins[0].get("joints", [])) if skins else 0
        row.update({
            "nodes": len(doc.get("nodes", [])),
            "meshes": len(doc.get("meshes", [])),
            "skins": len(skins),
            "skin0_joints": joints,
            "animations": len(doc.get("animations", [])),
            "json_ok": True,
        })
        row["ok"] = bool(joints >= 1074 and len(doc.get("meshes", [])) > 0)
    except Exception as exc:  # pragma: no cover - diagnostic path
        row.update({"ok": False, "error": repr(exc)})
    return row


def inspect_gltf(rel: str) -> dict[str, Any]:
    p = ROOT / rel
    row = check_file(rel, "gltf", 100)
    if not row["ok"]:
        return row
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        buffers = doc.get("buffers", [])
        uri = buffers[0].get("uri", "") if buffers else ""
        binary = p.parent / uri
        joints = len(doc.get("skins", [{}])[0].get("joints", [])) if doc.get("skins") else 0
        row.update({"nodes": len(doc.get("nodes", [])), "meshes": len(doc.get("meshes", [])), "skin0_joints": joints, "buffer": uri, "buffer_ok": binary.is_file() and binary.stat().st_size >= int(buffers[0].get("byteLength", 0)) if buffers else False})
        row["ok"] = bool(joints >= 1074 and row["buffer_ok"])
    except Exception as exc:  # pragma: no cover - diagnostic path
        row.update({"ok": False, "error": repr(exc)})
    return row


def inspect_media(rel: str, magic: bytes, kind: str) -> dict[str, Any]:
    row = check_file(rel, kind, len(magic))
    if row["ok"]:
        row["header_ok"] = (ROOT / rel).read_bytes()[: len(magic)] == magic
        row["ok"] = bool(row["header_ok"])
    return row


def main() -> int:
    rows: list[dict[str, Any]] = []
    rows.extend([
        check_file("TLOU2Codex.uproject", "ue_project", 50),
        check_file("Exports/Ellie_Patrol_Catalog_Exact.fbx", "fbx", 100),
        check_file("Blender/Ellie_Patrol_Catalog_Exact.blend", "blender", 100),
        check_file("Exports/Ellie_1074_SkeletonManifest.json", "skeleton_manifest", 100),
        check_file("Exports/Ellie_1074_RootMotion_AnimationProbe.fbx", "fbx_animation", 100),
        check_file("Exports/Ellie_Patrol_ExactAnimationPreview.gif", "gif", 100),
        check_file("Exports/Ellie_Patrol_RawRootCandidate_0FW.gif", "raw_root_candidate_gif", 100),
        check_file("Exports/Ellie_Patrol_Catalog_Exact_Preview.png", "png", 100),
    ])
    rows.extend([
        inspect_glb("Exports/Ellie_Patrol_Catalog_Exact.glb"),
        inspect_glb("Exports/Ellie_Patrol_ExactBody.glb"),
        inspect_gltf("Exports/Ellie_Patrol_Catalog_Exact.gltf"),
        inspect_gltf("Exports/Ellie_Patrol_ExactBody.gltf"),
    ])
    rows.extend([
        inspect_media("Exports/Ellie_Patrol_ExactAnimationPreview.gif", b"GIF8", "gif"),
        inspect_media("Exports/Ellie_Patrol_Catalog_Exact_Preview.png", b"\x89PNG\r\n\x1a\n", "png"),
        inspect_media("Content/TLOU2/Reference/captured_frame.png", b"\x89PNG\r\n\x1a\n", "capture_png"),
    ])

    tex_manifest_path = EXPORTS / "TexturesDecoded" / "texture_decode_manifest.json"
    tex_rows: list[dict[str, Any]] = []
    if tex_manifest_path.is_file():
        tex_rows = json.loads(tex_manifest_path.read_text(encoding="utf-8"))
    tex_ok = bool(tex_rows) and all(bool(r.get("decoded")) and Path(r.get("decoded_path", "")).is_file() for r in tex_rows)
    rows.append({"path": "Exports/TexturesDecoded/texture_decode_manifest.json", "kind": "texture_manifest", "ok": tex_ok, "decoded": len(tex_rows)})

    anim_manifest = EXPORTS / "AnimationSources" / "animation_source_manifest.json"
    anim_doc = json.loads(anim_manifest.read_text(encoding="utf-8")) if anim_manifest.is_file() else {}
    codec_count = sum(len(ch.get("codec", [])) for s in anim_doc.get("sources", []) for ch in s.get("chunks", []))
    raw_count = sum(sum(1 for r in ch.get("resources", []) if r.get("type") == "ANIM_RAWCHANNELS") for s in anim_doc.get("sources", []) for ch in s.get("chunks", []))
    rows.append({"path": "Exports/AnimationSources/animation_source_manifest.json", "kind": "animation_sources", "ok": len(anim_doc.get("sources", [])) >= 7 and codec_count >= 1164 and raw_count >= 1227, "sources": len(anim_doc.get("sources", [])), "codec_payloads": codec_count, "rawchannels": raw_count})

    ue_report_path = EXPORTS / "final_ue_verification.json"
    ue_doc = json.loads(ue_report_path.read_text(encoding="utf-8")) if ue_report_path.is_file() else {}
    rows.append({"path": "Exports/final_ue_verification.json", "kind": "ue_commandlet_report", "ok": bool(ue_doc.get("pass")), "errors": ue_doc.get("errors", [])})

    source_paks = list((ROOT / "Content" / "TLOU2" / "SourcePaks" / "Animations").rglob("*.pak"))
    rows.append({"path": "Content/TLOU2/SourcePaks/Animations", "kind": "source_paks", "ok": len(source_paks) >= 6, "pak_count": len(source_paks)})

    failed = [r for r in rows if not r.get("ok")]
    result = {"project": str(ROOT), "capture": "D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture", "checks": rows, "failed": len(failed), "pass": not failed}
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# Deliverable verification (2026-10-16)", "", f"Project: `{ROOT}`", "", "| Check | Kind | Status | Detail |", "|---|---|---|---|"]
    for r in rows:
        detail = ", ".join(f"{k}={v}" for k, v in r.items() if k not in {"path", "kind", "ok", "sha256"})
        lines.append(f"| `{r['path']}` | {r['kind']} | {'PASS' if r.get('ok') else 'FAIL'} | {detail} |")
    lines += ["", f"**Result:** {'PASS' if not failed else 'FAIL'} ({len(rows) - len(failed)}/{len(rows)} checks)", "", "The original ND compressed animation payloads remain byte-preserved evidence; this file-level check does not reinterpret their proprietary quantizer."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
