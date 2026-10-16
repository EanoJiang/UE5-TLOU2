import bpy, os
from mathutils import Vector

ROOT = r'D:/TLOU2_UE5_8_Codex'
BLEND = ROOT + '/Blender/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw.blend'
OUT_DIR = ROOT + '/Exports/RawRootCandidate0FWPreviewFrames'
OUT_GIF = ROOT + '/Exports/Ellie_Patrol_RawRootCandidate_0FW.gif'
OUT_REPORT = ROOT + '/Exports/Ellie_Patrol_RawRootCandidate_0FW_report.json'

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
os.makedirs(OUT_DIR, exist_ok=True)
if not scene.camera:
    bpy.ops.object.camera_add(location=(2.6, -4.6, 2.0))
    scene.camera = bpy.context.object
scene.camera.location = (2.6, -4.6, 2.0)
scene.camera.rotation_euler = (Vector((0, 0, 1.0)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()

n = scene.frame_end
picks = sorted(set([1, max(1, n // 4), max(1, n // 2), max(1, (3 * n) // 4), n]))
paths = []
for frame in picks:
    scene.frame_set(frame)
    path = os.path.join(OUT_DIR, f'frame_{frame:04d}.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    paths.append(path)

try:
    from PIL import Image, ImageDraw
    images = [Image.open(p).convert('RGB') for p in paths]
    for frame, image in zip(picks, images):
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 365, 34), fill=(0, 0, 0))
        draw.text((14, 14), f'Raw root candidate 0FW {frame:02d}/{n}', fill=(240, 240, 240))
    images[0].save(OUT_GIF, save_all=True, append_images=images[1:], duration=133, loop=0, optimize=True)
except Exception as exc:
    print('GIF_WARNING', repr(exc))

import json
json.dump({'clip': 'ellie-prone-lg-aim-strafe-0-fw', 'frames': n, 'fps': 30,
           'blend': BLEND, 'frame_pngs': paths, 'gif': OUT_GIF,
           'status': 'raw root trajectory candidate preview; source units and semantics unresolved'},
          open(OUT_REPORT, 'w', encoding='utf8'), indent=2)
print('RAW_ROOT_0FW_PREVIEW', picks, OUT_GIF)
