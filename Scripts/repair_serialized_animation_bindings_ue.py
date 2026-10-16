"""Persist single-node AnimSequence bindings in catalog maps.

``SkeletalMeshComponent.set_animation`` changes the live preview but, in UE
5.8's Python editor API, does not always serialize ``SingleAnimationPlayData``
when a level is saved.  This repair writes the struct explicitly and then
reloads each map to verify that ``anim_to_play`` survives serialization.
"""
import json
import os
import traceback
import unreal

ROOT = "D:/TLOU2_UE5_8_Codex"
MAPS = {
    "/Game/TLOU2/Maps/ElliePatrolCatalogSkeletal": "/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim",
    "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletal": "/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim",
    "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial": "/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim",
    "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate": "/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim",
}
OUT = os.path.join(ROOT, "Exports", "serialized_animation_bindings_repair.json")
out = {"maps": {}, "pass": False}


def set_anim(component, anim):
    data = component.get_editor_property("animation_data")
    data.set_editor_property("anim_to_play", anim)
    data.set_editor_property("saved_looping", True)
    data.set_editor_property("saved_playing", True)
    data.set_editor_property("saved_position", 0.0)
    data.set_editor_property("saved_play_rate", 1.0)
    component.set_editor_property("animation_data", data)
    component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    component.set_update_animation_in_editor(True)
    component.modify()


try:
    for map_path, anim_path in MAPS.items():
        anim = unreal.load_asset(anim_path)
        row = {"animation": anim_path, "before": [], "after": [], "errors": []}
        if not anim:
            row["errors"].append("missing animation")
            out["maps"][map_path] = row
            continue
        unreal.EditorLevelLibrary.load_level(map_path)
        actors = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(a, unreal.SkeletalMeshActor)]
        for actor in actors:
            comp = actor.skeletal_mesh_component
            data = comp.get_editor_property("animation_data")
            before = data.get_editor_property("anim_to_play")
            row["before"].append({"label": actor.get_actor_label(), "anim": str(before)})
            # The catalog plinth is intentionally static and does not share the
            # Ellie skeleton; all other skeletal actors are outfit chunks/body.
            mesh = comp.get_skeletal_mesh_asset()
            if mesh and mesh.get_editor_property("skeleton") == anim.get_editor_property("skeleton"):
                set_anim(comp, anim)
        unreal.EditorLevelLibrary.save_current_level()

        # Reload the level and verify serialization, not just the in-memory value.
        unreal.EditorLevelLibrary.load_level(map_path)
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if not isinstance(actor, unreal.SkeletalMeshActor):
                continue
            comp = actor.skeletal_mesh_component
            data = comp.get_editor_property("animation_data")
            got = data.get_editor_property("anim_to_play")
            mesh = comp.get_skeletal_mesh_asset()
            if mesh and mesh.get_editor_property("skeleton") == anim.get_editor_property("skeleton"):
                row["after"].append({"label": actor.get_actor_label(), "anim": str(got), "ok": got == anim})
                if got != anim:
                    row["errors"].append("binding did not survive reload: " + actor.get_actor_label())
        row["saved"] = not row["errors"]
        out["maps"][map_path] = row
    out["pass"] = all(not v.get("errors") for v in out["maps"].values())
except Exception as exc:
    out["error"] = repr(exc)
    out["traceback"] = traceback.format_exc()

with open(OUT, "w", encoding="utf-8") as fp:
    json.dump(out, fp, indent=2)
unreal.log("SERIALIZED_ANIMATION_BINDINGS " + json.dumps(out, ensure_ascii=False))
if not out.get("pass"):
    raise RuntimeError("serialized animation binding repair failed")
