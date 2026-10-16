"""Apply the decoded original 0FW local S/Q/T to the corrected meter rig.

Run with Blender. The original numerical animation is preserved in a separate
JSON. Blender quaternions are normalized only for building rotation matrices.
Non-driven bones inherit their corrected reference transform.
"""
import bpy
import csv
import json
import math
import os
import sys
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(r"D:/TLOU2_UE5_8_Codex")
CLIP = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "ellie-prone-lg-aim-strafe-0-fw"
IS_VIEWER = CLIP.startswith("model-viewer-")
OUT_LABEL = ("Ellie16_Patrol_OriginalViewerPose" if "ellie-16-patrol" in CLIP else "Ellie_Patrol_OriginalViewerPose") if IS_VIEWER else "Ellie_Patrol_Original_0FW"
SOURCE_BLEND = ROOT / "Blender/Ellie_Patrol_Catalog_CaptureMatched.blend"
DECODE = ROOT / "Exports/AnimationSources/DecodedOriginal" / (CLIP+".json")
REST = ROOT / "Exports/Ellie_AugmentedBindRest_SourceMatrices.json"
OUT_BLEND = ROOT / "Blender" / (OUT_LABEL+".blend")
OUT_FBX = ROOT / "Exports" / (OUT_LABEL+".fbx")
OUT_GLB = ROOT / "Exports" / (OUT_LABEL+".glb")
OUT_ANIM = ROOT / "Exports" / (OUT_LABEL+"_AnimationCarrier.fbx")
OUT_VERIFY = ROOT / "Exports" / (OUT_LABEL+"_blender_validation.json")
C = Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))


def source_matrix(scale, rotation_xyzw, translation):
    x,y,z,w = rotation_xyzw
    q = Quaternion((w,x,y,z))
    q.normalize()
    return Matrix.LocRotScale(Vector(translation), q, Vector(scale))


def local_frame(track, frame):
    # The final decoder writes constant S/T and 80 original rotations.
    return source_matrix(track["scale"], track["rotations_xyzw"][frame], track["translation"])


def action_curves(action):
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    curves=[]
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                curves.extend(bag.fcurves)
    return curves


def main():
    doc=json.loads(DECODE.read_text(encoding="utf-8"))
    rest=json.loads(REST.read_text(encoding="utf-8"))
    frames=int(doc.get("frame_count",80))
    rate=float(doc.get("sample_rate_hz",30) or 30)
    tracks=doc["tracks"]
    by_name={r["bone_name"]:r for r in rest["rows"]}
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    arm=next(o for o in bpy.data.objects if o.type=="ARMATURE")
    # Independently confirm the source really has the newly corrected rig.
    rest_error=max(max(abs(arm.data.bones[r["bone_name"]].matrix_local[i][j]-r["global_matrix_blender_meters"][i][j]) for i in range(4) for j in range(4)) for r in rest["rows"])
    # Blender edit-bone roll storage introduces ~2.8e-5 matrix error at the
    # nearly degenerate slot1_attach_offset helper; primary tracked bones are
    # below6e-6. The evaluated animation check below uses tighter bounds.
    human_rest_error=max(max(abs(arm.data.bones[r['bone_name']].matrix_local[i][j]-r['global_matrix_blender_meters'][i][j]) for i in range(4) for j in range(4)) for r in rest['rows'] if r.get('rig_owner') not in ('hoodie','backpack'))
    # Additional nearly degenerate owned helper rolls store at4.27e-5; keep a
    # separate gate so this never relaxes the original human reference check.
    if human_rest_error>3e-5 or rest_error>5e-5:
        raise RuntimeError(f"source bind rig does not match original S/Q/T: {rest_error}")
    arm.animation_data_clear()
    arm.location=(0,0,0)
    arm.rotation_euler=(0,0,0)
    arm.scale=(1,1,1)
    for obj in bpy.data.objects:
        if obj.type=="MESH" and any(m.type=="ARMATURE" and m.object==arm for m in obj.modifiers):
            world=obj.matrix_world.copy()
            obj.parent=arm
            obj.matrix_world=world
    for pose in arm.pose.bones:
        pose.matrix_basis=Matrix.Identity(4)
        pose.rotation_mode="QUATERNION"
    action=bpy.data.actions.new("AN_Original_"+CLIP.replace("-","_"))
    arm.animation_data_create()
    arm.animation_data.action=action
    action["source_clip"]=doc.get("clip","ellie-prone-lg-aim-strafe-0-fw")
    action["source_pak"]="model-viewer.pak" if IS_VIEWER else "anim-ellie-player-movement.pak"
    action["decode_status"]="original one-frame catalog pose; no invented idle" if IS_VIEWER else "original compressed clip decoded; native math verified; sparse source layer on reference pose"
    action["root_policy"]="source root transform retained; external raw root candidate is not mixed in"
    local_rest={}
    for bone in arm.data.bones:
        # Compensate the small edit-bone roll/storage error using the actual
        # rest matrix Blender evaluates, then apply the exact source local pose.
        local_rest[bone.name]=(bone.parent.matrix_local.inverted()@bone.matrix_local) if bone.parent else bone.matrix_local.copy()
    owned_rows=[r for r in rest['rows'] if r.get('rig_owner') in ('hoodie','backpack')]
    def expected_globals(frame):
        expected={}
        track_map={t['bone_name']:t for t in tracks}
        for row in rest['rows']:
            name=row['bone_name'];bone=arm.data.bones[name]
            if row.get('rig_owner') in ('hoodie','backpack'):
                anchor=row.get('human_anchor_name')
                if anchor:
                    expected[name]=expected[anchor] @ arm.data.bones[anchor].matrix_local.inverted() @ bone.matrix_local
                else:
                    expected[name]=expected[bone.parent.name] @ local_rest[name] if bone.parent else bone.matrix_local.copy()
            else:
                local=C@local_frame(track_map[name],frame)@C.transposed() if name in track_map else local_rest[name]
                expected[name]=expected[bone.parent.name] @ local if bone.parent else local
        return expected
    scene=bpy.context.scene
    scene.frame_start=1
    scene.frame_end=frames
    scene.render.fps=round(rate)
    scene.render.fps_base=1
    for frame in range(frames):
        for track in tracks:
            pose=arm.pose.bones[track["bone_name"]]
            animated=C@local_frame(track,frame)@C.transposed()
            pose.matrix_basis=local_rest[track["bone_name"]].inverted()@animated
            pose.keyframe_insert("location",frame=frame+1,group=pose.name)
            pose.keyframe_insert("rotation_quaternion",frame=frame+1,group=pose.name)
            pose.keyframe_insert("scale",frame=frame+1,group=pose.name)
        expected=expected_globals(frame)
        for row in owned_rows:
            name=row['bone_name'];pose=arm.pose.bones[name];parent=pose.parent
            local=expected[parent.name].inverted() @ expected[name] if parent else expected[name]
            pose.matrix_basis=local_rest[name].inverted() @ local
            for channel in ('location','rotation_quaternion','scale'):
                pose.keyframe_insert(channel,frame=frame+1,group=name)
    for curve in action_curves(action):
        for key in curve.keyframe_points:
            key.interpolation="LINEAR"
    # Check evaluated Blender local transforms against the original decoder at
    # every source frame, including parent motion and reference-pose inheritance.
    max_local_error=0.0
    max_global_error=0.0
    max_owned_global_error=0.0
    evaluated_rows=[]
    track_map={t["bone_name"]:t for t in tracks}
    for frame in range(frames):
        scene.frame_set(frame+1)
        bpy.context.view_layer.update()
        expected=expected_globals(frame)
        for row in rest["rows"]:
            name=row["bone_name"]
            local=C@local_frame(track_map[name],frame)@C.transposed() if name in track_map else local_rest[name]
            parent=row["parent_index"]
            actual=arm.pose.bones[name].matrix
            if name in track_map:
                actual_local=arm.pose.bones[row["bone_name"]].parent.matrix.inverted()@actual if parent>=0 else actual
                max_local_error=max(max_local_error,max(abs(actual_local[i][j]-local[i][j]) for i in range(4) for j in range(4)))
                max_global_error=max(max_global_error,max(abs(actual[i][j]-expected[name][i][j]) for i in range(4) for j in range(4)))
            if row.get('rig_owner') in ('hoodie','backpack'):
                max_owned_global_error=max(max_owned_global_error,max(abs(actual[i][j]-expected[name][i][j]) for i in range(4) for j in range(4)))
        root=arm.pose.bones["root"].matrix.translation
        evaluated_rows.append({"frame":frame,"time_s":frame/rate,"root_x_m":root.x,"root_y_m":root.y,"root_z_m":root.z})
    if max_local_error>2e-5 or max_global_error>3e-5 or max_owned_global_error>1e-4:
        raise RuntimeError(f"Blender pose round-trip error: local={max_local_error} global={max_global_error}")
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    model_meshes=[o for o in bpy.data.objects if o.type=="MESH" and any(m.type=="ARMATURE" and m.object==arm for m in o.modifiers)]
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for obj in model_meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=arm
    fbx_options=dict(use_selection=True,object_types={"ARMATURE","MESH"},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_step=1.0,bake_anim_simplify_factor=0.0,apply_unit_scale=True,axis_forward="-Z",axis_up="Y",primary_bone_axis="Y",secondary_bone_axis="X",use_custom_props=True)
    bpy.ops.export_scene.fbx(filepath=str(OUT_FBX),**fbx_options)
    bpy.ops.export_scene.gltf(filepath=str(OUT_GLB),export_format="GLB",use_selection=True,export_animations=True,export_all_influences=True)
    # A small geometry carrier makes UE animation import independent of the
    # large 31-mesh aggregate. It retains all 1,074 bone names and rest matrices.
    mesh=bpy.data.meshes.new("Original0FW_AnimationCarrier")
    mesh.from_pydata([(0,0,0),(.01,0,0),(0,.01,0)],[],[(0,1,2)])
    mesh.update()
    carrier=bpy.data.objects.new("Original0FW_AnimationCarrier",mesh)
    bpy.context.collection.objects.link(carrier)
    group=carrier.vertex_groups.new(name="root")
    group.add([0,1,2],1,"REPLACE")
    carrier.modifiers.new("Armature","ARMATURE").object=arm
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    carrier.select_set(True)
    bpy.context.view_layer.objects.active=arm
    bpy.ops.export_scene.fbx(filepath=str(OUT_ANIM),**fbx_options)
    bpy.data.objects.remove(carrier,do_unlink=True)
    with (ROOT/"Exports"/(OUT_LABEL+"_RootTrajectory.csv")).open("w",newline="",encoding="utf-8") as fp:
        writer=csv.DictWriter(fp,fieldnames=list(evaluated_rows[0]))
        writer.writeheader()
        writer.writerows(evaluated_rows)
    report={"pass":True,"source":str(DECODE),"source_blend":str(SOURCE_BLEND),"blend":str(OUT_BLEND),"fbx":str(OUT_FBX),"glb":str(OUT_GLB),"animation_carrier":str(OUT_ANIM),"frames":frames,"fps":rate,"driven_bones":len(tracks),"skeleton_bones":len(arm.data.bones),"rest_matrix_max_error":rest_error,"evaluated_local_matrix_max_error":max_local_error,"evaluated_global_matrix_max_error":max_global_error,"owned_rig_global_matrix_max_error":max_owned_global_error,"owned_rig_animated_nodes":len(owned_rows),"owned_animation_policy":"original owned reference plus declared human anchor deltas; cloth simulation absent from sparse source clip","root_motion_policy":"original one-frame root transform with zero displacement" if IS_VIEWER else "clip root is undriven and remains at source reference transform; no synthetic or external candidate trajectory added","source_clip_role":CLIP+" original one-frame pose,520 source S/Q/T bones" if IS_VIEWER else "sparse right-arm and right-finger layer on reference pose"}
    OUT_VERIFY.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("ORIGINAL_ANIMATION_BLENDER_VERIFY "+json.dumps(report))


if __name__=="__main__":
    main()
