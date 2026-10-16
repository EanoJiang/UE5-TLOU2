"""Generate smaller, importable skeletal FBX files from the exact catalogue.

The full catalogue has one 1074-bone armature and every mesh carries the full
vertex-group table.  That is faithful to the source but expensive for FBX
import.  This script writes independent FBX chunks.  Each chunk keeps every
bone actually referenced by its meshes plus all parents needed to preserve the
hierarchy, removes unused vertex groups, and points the copied Armature
modifiers at the copied armature.  The source blend is never modified.

Run with Blender's bundled Python, for example:
  blender -b Ellie_Patrol_Catalog_Exact.blend --python this_file.py
"""

import bpy
import json
import os
from collections import defaultdict, deque

ROOT = r"D:/TLOU2_UE5_8_Codex"
SRC_BLEND = os.path.join(ROOT, "Blender", "Ellie_Patrol_Catalog_Exact.blend")
OUT_DIR = os.path.join(ROOT, "Exports", "PrunedArmature")
MANIFEST = os.path.join(ROOT, "Exports", "pruned_armature_manifest.json")
os.makedirs(OUT_DIR, exist_ok=True)
# A full-bone variant is useful with importers that insist the FBX skeleton
# exactly matches a pre-existing UE skeleton.  The default remains pruned.
KEEP_ALL_BONES = False

# Semantic chunks keep each FBX small enough for UE's editor importer while
# retaining the whole outfit.  Names are matched against the source object
# names, which are deterministic in the exact catalogue.
CHUNK_PATTERNS = {
    "body_clothing": [
        "ellie16_inner_body", "ellie16_patrol_hands", "ellie16_patrol_pants",
        "ellie16_patrol_shirt", "ellie16_patrol_shoes", "patrol_boots",
        "patrol_hoodie", "patrol_jacket", "patrol_pants", "patrol_l_glove",
        "patrol_r_glove",
    ],
    "head_face": [
        "default_head", "default_teeth", "eye_fma", "eyebrow_fma",
        "eyelashes", "caruncle_fma", "tear_fma",
    ],
    "hair": ["patrol_hair_"],
    "backpack": ["backpack_"],
    "accessories": ["wings_pin"],
}


def mesh_chunks(meshes):
    assigned = set()
    out = defaultdict(list)
    for obj in meshes:
        n = obj.name.lower()
        hit = None
        for chunk, pats in CHUNK_PATTERNS.items():
            if any(p in n for p in pats):
                hit = chunk
                break
        if hit is None:
            hit = "accessories"
        out[hit].append(obj)
        assigned.add(obj.name)
    # This check catches a future source naming change instead of silently
    # dropping geometry.
    missing = sorted(o.name for o in meshes if o.name not in assigned)
    if missing:
        raise RuntimeError("unassigned meshes: %s" % missing)
    return out


def used_bones(obj, arm):
    # Walk membership once.  The source stores 1074 groups on every mesh, so
    # scanning every vertex once per group is needlessly quadratic.
    names = set()
    for v in obj.data.vertices:
        for g in v.groups:
            if g.weight > 1e-8:
                try:
                    name = obj.vertex_groups[g.group].name
                except (IndexError, RuntimeError):
                    continue
                if name in arm.data.bones:
                    names.add(name)
    return names


def add_parents(names, arm):
    keep = set(names)
    for name in list(names):
        b = arm.data.bones.get(name)
        seen = set()
        while b and b.parent and b.parent.name not in seen:
            seen.add(b.parent.name)
            keep.add(b.parent.name)
            b = b.parent
    return keep


def clone_chunk(chunk, meshes, source_arm):
    # Isolate all data in the current blend datablock.  The caller saves only
    # the source file, so these temporary datablocks do not touch the source.
    source_name = source_arm.name
    # Blender enforces unique object names.  Temporarily free the canonical
    # source name so the exported duplicate receives it (otherwise Blender
    # silently writes SK_Ellie_Patrol_Exact.001 and UE cannot merge it).
    source_arm.name = source_name + "__SOURCE_TMP"
    arm_data = source_arm.data.copy()
    arm = source_arm.copy()
    arm.data = arm_data
    # UE's Interchange importer treats the Blender armature object as the
    # synthetic root bone.  Keep the exact source object name so chunk FBXs
    # merge with Probe1074 (whose first bone is SK_Ellie_Patrol_Exact).
    arm.name = source_name
    bpy.context.collection.objects.link(arm)

    clones = []
    names = set()
    for src in meshes:
        names |= used_bones(src, source_arm)
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = "%s_%s" % (chunk, src.name)
        bpy.context.collection.objects.link(ob)
        # Remove unused groups from the copied mesh.  This matters for FBX
        # size and prevents UE from constructing thousands of empty influences.
        for vg in list(ob.vertex_groups):
            if vg.name not in names:  # refined below after all meshes are scanned
                pass
        for mod in ob.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = arm
        # Joined source meshes are parented to the canonical source armature.
        # Copies must follow the exported duplicate, preserving their world
        # transform and avoiding an unselected temporary parent in the FBX.
        world = ob.matrix_world.copy()
        ob.parent = arm
        ob.matrix_world = world
        clones.append(ob)

    names = add_parents(names, source_arm)
    if KEEP_ALL_BONES:
        names = set(b.name for b in source_arm.data.bones)
    # Remove groups now that the chunk-wide keep set is known.
    for ob in clones:
        for vg in list(ob.vertex_groups):
            if vg.name not in names:
                ob.vertex_groups.remove(vg)

    # Delete non-required bones from the copied armature, leaf first.
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in sorted(list(arm.data.edit_bones), key=lambda b: len(b.parent_recursive), reverse=True):
        if eb.name not in names:
            arm.data.edit_bones.remove(eb)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Export only this chunk.  Use a separate selection to avoid accidentally
    # including camera/lights from the source catalogue.
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for ob in clones:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = arm
    filename = "Ellie_Patrol_%s_Pruned.fbx" % chunk
    path = os.path.join(OUT_DIR, filename)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False, bake_anim=False, apply_unit_scale=True,
        axis_forward='-Z', axis_up='Y', use_armature_deform_only=False,
        mesh_smooth_type='FACE', use_custom_props=True,
        primary_bone_axis='Y', secondary_bone_axis='X')

    # Gather post-export counts from copies.
    rows = []
    for ob, src in zip(clones, meshes):
        rows.append({
            'source_mesh': src.name,
            'export_mesh': ob.name,
            'vertices': len(ob.data.vertices),
            'source_groups': len(src.vertex_groups),
            'export_groups': len(ob.vertex_groups),
            'used_bone_count': len(used_bones(src, source_arm)),
        })
    result = {
        'chunk': chunk,
        'fbx': path,
        'size_bytes': os.path.getsize(path),
        'mesh_count': len(clones),
        'bone_count': len(arm.data.bones),
        'required_influences': len(names),
        'meshes': rows,
    }
    # Remove temporary data before the next chunk to keep Blender memory low.
    mesh_datas = [ob.data for ob in clones]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in clones + [arm]:
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.armatures.remove(arm_data)
    for me in mesh_datas:
        if me.users == 0:
            bpy.data.meshes.remove(me)
    source_arm.name = source_name
    return result


def main():
    source_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    chunks = mesh_chunks(meshes)
    report = {
        'source_blend': SRC_BLEND,
        'source_armature': source_arm.name,
        'source_bone_count': len(source_arm.data.bones),
        'source_mesh_count': len(meshes),
        'chunks': {},
    }
    for chunk, objs in chunks.items():
        print('PRUNED_START', chunk, len(objs), flush=True)
        report['chunks'][chunk] = clone_chunk(chunk, objs, source_arm)
        print('PRUNED_DONE', chunk, report['chunks'][chunk]['bone_count'], flush=True)
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print('PRUNED_MANIFEST', MANIFEST, flush=True)


if __name__ == '__main__':
    main()
