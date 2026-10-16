import bpy, csv, json, os
from mathutils import Vector

ROOT = r'D:/TLOU2_UE5_8_Codex'
SRC = os.path.join(ROOT, 'Exports', 'AnimationSources', 'DecodedRawChannels', 'named_root_trajectory_samples.json')
OUT_BLEND = os.path.join(ROOT, 'Blender', 'Ellie_Patrol_RawRootCandidate_90LFW.blend')
OUT_FBX = os.path.join(ROOT, 'Exports', 'Ellie_1074_RawRootCandidate_ellie-prone-lg-aim-strafe-90l-fw.fbx')
OUT_CSV = os.path.join(ROOT, 'Exports', 'Ellie_1074_RawRootCandidate_ellie-prone-lg-aim-strafe-90l-fw.csv')
OUT_GIF = os.path.join(ROOT, 'Exports', 'Ellie_Patrol_RawRootCandidate_90LFW.gif')
FRAME_DIR = os.path.join(ROOT, 'Exports', 'RawRootCandidatePreviewFrames')
SOURCE_BLEND = os.path.join(ROOT, 'Blender', 'Ellie_Patrol_Catalog_Exact.blend')
CLIP = 'ellie-prone-lg-aim-strafe-90l-fw'

with open(SRC, 'r', encoding='utf-8') as f:
    rows = json.load(f)
row = next(r for r in rows if r.get('anim_name') == CLIP and r.get('codec', {}).get('magic') == '0x41430102')
samples = row['root_dynamic_samples']
codec = row['codec']
fps = float(codec.get('sample_rate') or 30.0)
period = float(codec.get('sample_period') or (1.0 / fps))

bpy.ops.wm.open_mainfile(filepath=SOURCE_BLEND)
scene = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = None
action = bpy.data.actions.new('AN_Ellie_RawRootCandidate_90LFW')
arm.animation_data.action = action
action['source_animation'] = CLIP
action['source_pak'] = row['source']
action['root_channel_hash'] = '0x509903bb65ac341e'
action['root_format'] = row['root_format']
action['codec_frames'] = int(codec['frames'])
action['codec_sample_rate_hz'] = fps
action['codec_sample_period_s'] = period
action['decode_status'] = 'raw_half_pair_direct_candidate; proprietary interpolation and units unresolved'
action['bone_map_status'] = 'root channel identity only; no source bone name asserted'

root = arm.pose.bones.get('root')
if root is None:
    raise RuntimeError('root bone not found')
for i, pair in enumerate(samples):
    frame = i + 1
    root.location = (float(pair[0]), float(pair[1]), 0.0)
    root.keyframe_insert(data_path='location', frame=frame, group='root')
scene.frame_start = 1
scene.frame_end = len(samples)
scene.render.fps = max(1, int(round(fps)))
scene['raw_root_candidate_source'] = CLIP
scene['raw_root_candidate_warning'] = 'Values are raw half streams; do not treat as final game-space root motion.'

os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

# Export a geometry-bearing FBX so the candidate can be reviewed beside the exact model.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'ARMATURE', 'MESH'}:
        o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=OUT_FBX, use_selection=True,
    object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False, bake_anim=True,
    bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False, bake_anim_step=1.0,
    bake_anim_simplify_factor=0.0, apply_unit_scale=True,
    axis_forward='-Z', axis_up='Y', primary_bone_axis='Y',
    secondary_bone_axis='X', use_custom_props=True)

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['clip', 'root_hash', 'format', 'sample_index', 'time_s', 'value0_raw_half', 'value1_raw_half', 'value2_assigned', 'units_status'])
    for i, pair in enumerate(samples):
        w.writerow([CLIP, '0x509903bb65ac341e', row['root_format'], i, i * period,
                    pair[0], pair[1], 0.0, 'unresolved'])

# Render a compact audit GIF from the exact outfit with this candidate root track.
try:
    from PIL import Image, ImageDraw
    os.makedirs(FRAME_DIR, exist_ok=True)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 512; scene.render.resolution_y = 512; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    if not scene.camera:
        bpy.ops.object.camera_add(location=(2.6, -4.6, 2.0)); scene.camera = bpy.context.object
    scene.camera.location = (2.6, -4.6, 2.0)
    scene.camera.rotation_euler = (Vector((0, 0, 1.0)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    picks = sorted(set([1, max(1, len(samples)//4), max(1, len(samples)//2), max(1, (3*len(samples))//4), len(samples)]))
    paths=[]
    for frame in picks:
        scene.frame_set(frame)
        path=os.path.join(FRAME_DIR, f'frame_{frame:04d}.png')
        scene.render.filepath=path; bpy.ops.render.render(write_still=True); paths.append(path)
    imgs=[Image.open(p).convert('RGB') for p in paths]
    for frame,im in zip(picks,imgs):
        d=ImageDraw.Draw(im); d.rectangle((8,8,330,34),fill=(0,0,0)); d.text((14,14),f'Raw root candidate {frame:02d}/{len(samples)}',fill=(240,240,240))
    imgs[0].save(OUT_GIF,save_all=True,append_images=imgs[1:],duration=max(1,int(1000*period*len(samples)/len(picks))),loop=0,optimize=True)
except Exception as e:
    print('PREVIEW_WARNING', repr(e))

report = {'clip': CLIP, 'source': row['source'], 'root_hash': '0x509903bb65ac341e',
          'format': row['root_format'], 'frames': len(samples), 'fps': fps,
          'period_s': period, 'duration_s': (len(samples)-1)*period,
          'fbx': OUT_FBX, 'blend': OUT_BLEND, 'csv': OUT_CSV, 'gif': OUT_GIF,
          'status': 'raw half pair candidate; not a completed game animation decode'}
with open(os.path.join(ROOT, 'Exports', 'Ellie_Patrol_RawRootCandidate_90LFW_report.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)
print('RAW_ROOT_CANDIDATE', json.dumps(report))
