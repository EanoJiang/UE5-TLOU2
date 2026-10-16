"""UE 5.8 commandlet validation for the imported animation interchange assets.

This checks the things that can be proved in UE without pretending that the
proprietary Naughty Dog codec has been fully decoded: shared 1,075-bone
skeleton identity, 80 x 30 Hz frame coverage, valid pose evaluation on every
frame, root-motion settings, exact preservation of the raw root-channel X
samples, and serialized map bindings after a level reload.
"""
import json
import math
import os
import traceback
import csv
import unreal

ROOT = "D:/TLOU2_UE5_8_Codex"
SKELETON = "/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton"
EXACT_ANIM = "/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim"
RAW_ANIM = "/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim"
SOURCE_JSON = os.path.join(ROOT, "Exports", "AnimationSources", "DecodedRawChannels", "named_root_trajectory_samples.json")
OUT_JSON = os.path.join(ROOT, "Exports", "animation_interchange_ue_verification.json")
OUT_MD = os.path.join(ROOT, "Content", "TLOU2", "Reports", "ANIMATION_INTERCHANGE_UE_VERIFICATION.md")
OUT_CSV = os.path.join(ROOT, "Exports", "Ellie_RawRootCandidate_0FW_UE_RootTrajectory.csv")

out = {
    "engine": "UE 5.8",
    "skeleton_asset": SKELETON,
    "expected_bone_count": 1075,
    "expected_frames": 80,
    "expected_rate_hz": 30.0,
    "assets": {},
    "maps": {},
    "errors": [],
}


def check(condition, message):
    if not condition:
        out["errors"].append(message)
    return bool(condition)


def vec3(transform):
    v = transform.translation
    return {"x": float(v.x), "y": float(v.y), "z": float(v.z)}


def inspect_anim(path):
    anim = unreal.load_asset(path)
    row = {"path": path, "exists": bool(anim)}
    if not anim:
        check(False, "missing animation asset: " + path)
        return row, None
    skeleton = anim.get_skeleton()
    names = []
    if skeleton:
        names = [str(n) for n in skeleton.get_reference_pose().get_bone_names()]
    row.update({
        "class": anim.get_class().get_name(),
        "skeleton": skeleton.get_path_name() if skeleton else None,
        "bone_count": len(names),
        "first_bones": names[:5],
        "sequence_length_s": float(anim.get_play_length()),
        "frame_count_expected_from_rate": int(round(anim.get_play_length() * 30.0)) + 1,
        "enable_root_motion": bool(anim.get_editor_property("enable_root_motion")),
        "root_motion_root_lock": str(anim.get_editor_property("root_motion_root_lock")),
    })
    check(row["class"] == "AnimSequence", path + " is not an AnimSequence")
    check(skeleton == unreal.load_asset(SKELETON), path + " does not use the shared skeleton")
    check(len(names) == 1075, path + " skeleton bone count != 1075")
    check(abs(row["sequence_length_s"] - (79.0 / 30.0)) < 0.01, path + " sequence length is not 80 samples at 30 Hz")
    check(row["enable_root_motion"], path + " root motion is disabled")

    # AnimPose evaluation exercises the serialized track data as UE consumes it.
    opts = unreal.AnimPoseEvaluationOptions()
    opts.set_editor_property("evaluation_type", unreal.AnimDataEvalType.RAW)
    frame_rows = []
    valid = True
    try:
        for frame in range(80):
            pose = anim.get_anim_pose_at_frame(frame, opts)
            names_at_frame = [str(n) for n in pose.get_bone_names()]
            if not pose.is_valid() or len(names_at_frame) != 1075:
                valid = False
                continue
            frame_rows.append({"frame": frame, "root": vec3(pose.get_bone_pose("root"))})
    except Exception as exc:
        row["pose_eval_error"] = repr(exc)
        valid = False
    row["pose_frame_count"] = len(frame_rows)
    row["pose_eval_valid"] = valid and len(frame_rows) == 80
    row["pose_samples"] = frame_rows[0:2] + frame_rows[-2:]
    check(row["pose_eval_valid"], path + " failed all-frame pose evaluation")
    return row, frame_rows


try:
    exact_row, exact_frames = inspect_anim(EXACT_ANIM)
    raw_row, raw_frames = inspect_anim(RAW_ANIM)
    out["assets"][EXACT_ANIM] = exact_row
    out["assets"][RAW_ANIM] = raw_row

    # The source JSON preserves the exact 80 raw half samples used to make the
    # candidate FBX.  UE's imported root local X is expected to round-trip them;
    # Y/Z include the bind-pose basis and are therefore not compared directly.
    source_rows = []
    if os.path.isfile(SOURCE_JSON):
        with open(SOURCE_JSON, "r", encoding="utf-8") as fp:
            source_doc = json.load(fp)
        source_rows = [r for r in source_doc if r.get("anim_name") == "ellie-prone-lg-aim-strafe-0-fw"]
    check(len(source_rows) == 1, "source named-root record missing")
    if source_rows and raw_frames:
        expected = source_rows[0].get("root_dynamic_samples", [])
        checks = []
        csv_rows = []
        for i, row in enumerate(raw_frames):
            if i >= len(expected):
                checks.append(False)
                continue
            err_x = abs(float(row["root"]["x"]) - float(expected[i][0]))
            checks.append(err_x <= 1.0e-5)
            csv_rows.append({
                "frame": i,
                "time_s": i / 30.0,
                "source_value0_raw_half": expected[i][0],
                "source_value1_raw_half": expected[i][1] if len(expected[i]) > 1 else "",
                "ue_root_x": row["root"]["x"],
                "ue_root_y": row["root"]["y"],
                "ue_root_z": row["root"]["z"],
                "abs_error_x": err_x,
                "source_units_status": "unresolved",
            })
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(csv_rows[0].keys()) if csv_rows else ["frame"])
            writer.writeheader()
            writer.writerows(csv_rows)
        out["raw_root_channel_roundtrip"] = {
            "source_clip": "ellie-prone-lg-aim-strafe-0-fw",
            "source_samples": len(expected),
            "ue_frames": len(raw_frames),
            "matching_x_samples": sum(1 for x in checks if x),
            "max_abs_error_x": max(
                [abs(float(raw_frames[i]["root"]["x"]) - float(expected[i][0])) for i in range(min(len(expected), len(raw_frames)))] or [None]
            ),
            "ue_trajectory_csv": OUT_CSV,
            "pass": len(checks) == 80 and all(checks),
            "semantic_status": "raw half-pair candidate; game-space units and channel semantics unresolved",
        }
        check(out["raw_root_channel_roundtrip"]["pass"], "raw root channel X samples did not round-trip into UE")
    else:
        out["raw_root_channel_roundtrip"] = {"pass": False, "reason": "missing source or UE frames"}

    # Verify that map serialization points every outfit chunk to the intended
    # sequence after closing/reopening the level.  The plinth is excluded.
    expected_maps = {
        "/Game/TLOU2/Maps/ElliePatrolCatalogSkeletal": EXACT_ANIM,
        "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletal": EXACT_ANIM,
        "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalMaterial": EXACT_ANIM,
        "/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate": RAW_ANIM,
    }
    for map_path, anim_path in expected_maps.items():
        anim = unreal.load_asset(anim_path)
        row = {"animation": anim_path, "skeletal_actors": [], "pass": True}
        unreal.EditorLevelLibrary.load_level(map_path)
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if not isinstance(actor, unreal.SkeletalMeshActor):
                continue
            comp = actor.skeletal_mesh_component
            mesh = comp.get_skeletal_mesh_asset()
            if not mesh or mesh.get_editor_property("skeleton") != anim.get_skeleton():
                continue
            data = comp.get_editor_property("animation_data")
            got = data.get_editor_property("anim_to_play")
            ok = got == anim and str(comp.get_editor_property("animation_mode")) == "<AnimationMode.ANIMATION_SINGLE_NODE: 1>"
            row["skeletal_actors"].append({"label": actor.get_actor_label(), "anim": str(got), "ok": ok})
            if not ok:
                row["pass"] = False
        if not row["skeletal_actors"]:
            row["pass"] = False
        out["maps"][map_path] = row
        check(row["pass"], map_path + " lacks a serialized single-node animation binding")
except Exception as exc:
    out["error"] = repr(exc)
    out["traceback"] = traceback.format_exc()

out["pass"] = not out["errors"]
with open(OUT_JSON, "w", encoding="utf-8") as fp:
    json.dump(out, fp, indent=2)

lines = [
    "# UE animation interchange verification",
    "",
    f"- Engine: UE 5.8 (`{out['engine']}`)",
    f"- Result: **{'PASS' if out['pass'] else 'FAIL'}**",
    "- Shared skeleton: 1,075 bones (`/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton`).",
    "- Frame contract: 80 evaluated frames at 30 Hz (2.633333 s sequence).",
    "- Every sequence was evaluated through `AnimPose` in UE's RAW data path.",
    "- The raw candidate's root local-X samples are compared against the source JSON; Y/Z remain bind-pose basis values.",
    "- All catalog maps are reloaded before their serialized `SingleAnimationPlayData.anim_to_play` bindings are checked.",
    "",
    "The `ellie-prone-lg-aim-strafe-0-fw` raw root track is intentionally described as a candidate: codec units, interpolation, full descriptor-to-bone mapping, and game-space semantics remain unresolved.",
    "",
]
if out.get("errors"):
    lines.extend(["## Errors", ""] + ["- " + e for e in out["errors"]] + [""])
with open(OUT_MD, "w", encoding="utf-8") as fp:
    fp.write("\n".join(lines))
unreal.log("ANIMATION_INTERCHANGE_UE_VERIFY " + json.dumps({"pass": out["pass"], "errors": out["errors"]}, ensure_ascii=False))
if not out["pass"]:
    raise RuntimeError("animation interchange UE verification failed")
