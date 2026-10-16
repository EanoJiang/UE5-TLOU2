"""Build a catalog map that plays the decoded raw root-channel candidate.

The sequence is intentionally kept separate from the verified interchange probe:
this map is a review surface for the 80-frame raw channel candidate extracted
from ``ellie-prone-lg-aim-strafe-0-fw``.  It uses the same five shared-skeleton
outfit chunks, materials, backdrop, plinth, and instruction strip as the final
catalog map so reviewers can inspect trajectory and presentation side by side.
"""
import json
import os
import traceback
import unreal

ROOT = "D:/TLOU2_UE5_8_Codex"
MAP = "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate"
ANIM = "/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim"
CHUNKS = [
    "/Game/TLOU2/Pruned1074/body_clothing/Ellie_Patrol_body_clothing_Pruned",
    "/Game/TLOU2/Pruned1074/head_face/Ellie_Patrol_head_face_Pruned",
    "/Game/TLOU2/Pruned1074/hair/Ellie_Patrol_hair_Pruned",
    "/Game/TLOU2/Pruned1074/backpack/Ellie_Patrol_backpack_Pruned",
    "/Game/TLOU2/Pruned1074/accessories/Ellie_Patrol_accessories_Pruned",
]
OUT = os.path.join(ROOT, "Exports", "raw_root_candidate_catalog_map_result.json")

out = {
    "map": MAP,
    "animation": ANIM,
    "animation_status": "raw root trajectory candidate; unresolved units/channel semantics",
    "source_clip": "ellie-prone-lg-aim-strafe-0-fw",
    "source_pak": "anim-ellie-player-movement.pak",
    "actors": [],
    "material_slots": 0,
    "material_bindings": 0,
    "ui": {},
}


def add_actor_component_mesh(mesh, label):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    actor.set_actor_label(label)
    comp = actor.skeletal_mesh_component
    comp.set_editor_property("skeletal_mesh", mesh)
    if anim:
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        data = comp.get_editor_property("animation_data")
        data.set_editor_property("anim_to_play", anim)
        data.set_editor_property("saved_looping", True)
        data.set_editor_property("saved_playing", True)
        data.set_editor_property("saved_position", 0.0)
        data.set_editor_property("saved_play_rate", 1.0)
        comp.set_editor_property("animation_data", data)
        comp.set_update_animation_in_editor(True)
        comp.play(True)
    bound = 0
    for i, slot in enumerate(mesh.get_editor_property("materials")):
        out["material_slots"] += 1
        slot_name = str(slot.get_editor_property("material_slot_name"))
        mat = mats.get(slot_name) if slot_name.startswith("M_ND_") else None
        if mat:
            comp.set_material(i, mat)
            bound += 1
            out["material_bindings"] += 1
    out["actors"].append({"mesh": mesh.get_path_name(), "actor": actor.get_path_name(), "bound_materials": bound})


try:
    unreal.EditorLevelLibrary.new_level(MAP)
    anim = unreal.load_asset(ANIM)
    mats = {}
    for p in unreal.EditorAssetLibrary.list_assets("/Game/TLOU2/Materials/Exact", recursive=True):
        a = unreal.load_asset(p)
        if a and a.get_name().startswith("M_ND_"):
            mats[a.get_name()] = a
    for p in CHUNKS:
        mesh = unreal.load_asset(p)
        if isinstance(mesh, unreal.SkeletalMesh):
            add_actor_component_mesh(mesh, "Ellie_Patrol_RawRootCandidate_" + mesh.get_name())

    # Capture-facing backdrop and lighting.
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    frame_mat = unreal.load_asset("/Game/TLOU2/Materials/M_CapturedFrame")
    if plane:
        bg = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(220, 0, 120), unreal.Rotator(0, 90, 0)
        )
        bg.set_actor_label("Captured_Frame_Backdrop")
        bg.static_mesh_component.set_editor_property("static_mesh", plane)
        bg.set_actor_scale3d(unreal.Vector(2.8, 2.0, 1.0))
        if frame_mat:
            bg.static_mesh_component.set_material(0, frame_mat)
    dl = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(150, -250, 250), unreal.Rotator(-35, -25, 0)
    )
    dl.set_actor_label("Catalog_Directional_Light")
    dl.get_components_by_class(unreal.LightComponent)[0].set_editor_property("intensity", 8.0)
    pl = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(-150, -100, 180), unreal.Rotator(0, 0, 0)
    )
    pl.set_actor_label("Catalog_Fill_Light")
    pl.get_components_by_class(unreal.LightComponent)[0].set_editor_property("intensity", 1200.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(260, -520, 160), unreal.Rotator(-8, 27, 0)
    )
    cam.set_actor_label("Catalog_Camera")

    # Reuse the capture-facing presentation assets where available.
    plinth = unreal.load_asset("/Game/TLOU2/Proxy/Catalog_Plinth")
    if plinth:
        a = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
        )
        a.set_actor_label("CatalogUI_Presentation_Plinth")
        a.skeletal_mesh_component.set_editor_property("skeletal_mesh", plinth)
        out["ui"]["plinth"] = a.get_path_name()
    inst_mat = unreal.load_asset("/Game/TLOU2/Materials/MI_CatalogInstructionBar")
    if plane and inst_mat:
        a = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(0, -30, -72), unreal.Rotator(90, 0, 0)
        )
        a.set_actor_label("CatalogUI_CapturedInstructionBar")
        a.static_mesh_component.set_editor_property("static_mesh", plane)
        a.static_mesh_component.set_material(0, inst_mat)
        a.set_actor_scale3d(unreal.Vector(9.6, 0.66, 1.0))
        out["ui"]["instruction_bar"] = a.get_path_name()

    unreal.EditorLevelLibrary.save_current_level()
    out["saved"] = True
except Exception as exc:
    out["saved"] = False
    out["error"] = repr(exc)
    out["traceback"] = traceback.format_exc()

with open(OUT, "w", encoding="utf-8") as fp:
    json.dump(out, fp, indent=2)
unreal.log("RAW_ROOT_CANDIDATE_CATALOG_MAP_DONE " + json.dumps(out, ensure_ascii=False))
if not out.get("saved"):
    raise RuntimeError(out.get("error", "map build failed"))
