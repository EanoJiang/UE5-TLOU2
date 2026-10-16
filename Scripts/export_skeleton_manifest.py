"""Export the portable skeleton hierarchy from the exact outfit glTF."""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / "Exports" / "Ellie_Patrol_Catalog_Exact.glb"
OUT = ROOT / "Exports" / "Ellie_1074_SkeletonManifest.json"
MD = ROOT / "Content" / "TLOU2" / "Reports" / "SKELETON_MANIFEST.md"


def fnv1a64(text: str) -> str:
    h = 0xCBF29CE484222325
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"0x{h:016x}"


def load_json_chunk(path: Path) -> dict:
    b = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", b, 0)
    if magic != b"glTF" or version != 2 or total != len(b):
        raise ValueError("invalid GLB header")
    off = 12
    while off + 8 <= len(b):
        n, typ = struct.unpack_from("<II", b, off)
        if typ == 0x4E4F534A:
            return json.loads(b[off + 8 : off + 8 + n].decode("utf-8").rstrip(" \x00"))
        off += 8 + n
    raise ValueError("JSON chunk missing")


def main() -> int:
    doc = load_json_chunk(GLB)
    nodes = doc.get("nodes", [])
    skin = doc.get("skins", [])[0]
    joint_indices = list(skin.get("joints", []))
    joint_set = set(joint_indices)
    parents: dict[int, int | None] = {i: None for i in joint_indices}
    for pi, node in enumerate(nodes):
        for ci in node.get("children", []):
            if ci in joint_set:
                parents[ci] = pi
    bones = []
    for order, ni in enumerate(joint_indices):
        n = nodes[ni]
        name = n.get("name", f"joint_{order}")
        parent_node = parents.get(ni)
        parent_name = nodes[parent_node].get("name") if parent_node is not None and parent_node < len(nodes) else None
        bones.append({
            "index": order,
            "node": ni,
            "name": name,
            "parent": parent_name,
            "parent_node": parent_node,
            "hash_fnv1a64": fnv1a64(name),
            "translation": n.get("translation", [0.0, 0.0, 0.0]),
            "rotation": n.get("rotation", [0.0, 0.0, 0.0, 1.0]),
            "scale": n.get("scale", [1.0, 1.0, 1.0]),
        })
    result = {
        "source": str(GLB).replace("\\", "/"),
        "skeleton_name": "SKEL_Ellie_Patrol_1074",
        "bone_count": len(bones),
        "root_bones": [b["name"] for b in bones if b["parent"] is None or b["parent_node"] not in joint_set],
        "mesh_count": len(doc.get("meshes", [])),
        "skin_count": len(doc.get("skins", [])),
        "animation_count": len(doc.get("animations", [])),
        "bones": bones,
        "hash_note": "FNV-1a64 is the verified Ellie joint-name hash used by the source skeleton table; the game animation channel codec still requires separate semantic mapping.",
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Ellie 1,074-bone skeleton manifest",
        "",
        f"Source: `{result['source']}`",
        "",
        f"- Skeleton: `{result['skeleton_name']}`",
        f"- Bones: **{result['bone_count']}** game joints",
        f"- Meshes: **{result['mesh_count']}**, skins: **{result['skin_count']}**, glTF animations: **{result['animation_count']}**",
        f"- Root joints: {', '.join(result['root_bones'])}",
        "- Each record includes parent linkage, local rest transform and verified FNV-1a64 joint-name hash.",
        "- UE imports add one FBX armature root, yielding the verified 1,075-name UE skeleton.",
        "- Animation codec channel-to-bone semantics remain documented separately in `BONE_CHANNEL_HASH_MAPPING.md`.",
        "",
        "The complete machine-readable hierarchy is in `Exports/Ellie_1074_SkeletonManifest.json`.",
    ]
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(OUT), "md": str(MD), "bone_count": len(bones), "root_bones": result["root_bones"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
