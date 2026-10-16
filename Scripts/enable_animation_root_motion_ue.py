import json
import os
import traceback
import unreal

ROOT = "D:/TLOU2_UE5_8_Codex"
ASSETS = {
    "/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim": unreal.RootMotionRootLock.REF_POSE,
    "/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim": unreal.RootMotionRootLock.ZERO,
}
out = {"assets": {}, "pass": False}
try:
    for path, lock in ASSETS.items():
        anim = unreal.load_asset(path)
        row = {"path": path, "exists": bool(anim)}
        if anim:
            anim.set_editor_property("enable_root_motion", True)
            anim.set_editor_property("root_motion_root_lock", lock)
            unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
            row.update({
                "enable_root_motion": bool(anim.get_editor_property("enable_root_motion")),
                "root_motion_root_lock": str(anim.get_editor_property("root_motion_root_lock")),
                "sequence_length": float(anim.get_editor_property("sequence_length")),
                "skeleton": anim.get_skeleton().get_path_name() if anim.get_skeleton() else None,
            })
            row["ok"] = row["enable_root_motion"]
        else:
            row["ok"] = False
        out["assets"][path] = row
    out["pass"] = all(v.get("ok") for v in out["assets"].values())
except Exception as exc:
    out["error"] = repr(exc)
    out["traceback"] = traceback.format_exc()
with open(os.path.join(ROOT, "Exports", "animation_root_motion_settings.json"), "w", encoding="utf-8") as fp:
    json.dump(out, fp, indent=2)
unreal.log("ANIMATION_ROOT_MOTION_SETTINGS " + json.dumps(out, ensure_ascii=False))
if not out.get("pass"):
    raise RuntimeError("failed to enable root motion settings")
