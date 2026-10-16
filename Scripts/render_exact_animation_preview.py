import bpy, os, math, json
from mathutils import Vector
from PIL import Image, ImageDraw

ROOT = r'D:/TLOU2_UE5_8_Codex'
BLEND = os.path.join(ROOT, 'Blender', 'Ellie_Patrol_Catalog_Exact.blend')
OUT = os.path.join(ROOT, 'Exports')
FRAME_DIR = os.path.join(OUT, 'ExactAnimationPreviewFrames')
GIF = os.path.join(OUT, 'Ellie_Patrol_ExactAnimationPreview.gif')
os.makedirs(FRAME_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world.color = (0.012, 0.012, 0.012)

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if not scene.camera:
    bpy.ops.object.camera_add(location=(2.6, -4.6, 2.0))
    scene.camera = bpy.context.object
cam = scene.camera
cam.location = (2.6, -4.6, 2.0)
cam.data.lens = 58
cam.rotation_euler = (Vector((0, 0, 1.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()

frames = list(range(1, 81, 5))
paths = []
for frame in frames:
    scene.frame_set(frame)
    fn = os.path.join(FRAME_DIR, f'frame_{frame:04d}.png')
    scene.render.filepath = fn
    bpy.ops.render.render(write_still=True)
    paths.append(fn)

imgs = [Image.open(p).convert('RGB') for p in paths]
# Add a small frame/time label so the preview is auditable and useful in reviews.
for frame, im in zip(frames, imgs):
    d = ImageDraw.Draw(im)
    d.rectangle((8, 8, 165, 34), fill=(0, 0, 0))
    d.text((14, 14), f'Exact outfit  frame {frame:02d}/80', fill=(240, 240, 240))
imgs[0].save(GIF, save_all=True, append_images=imgs[1:], duration=1000/30*5, loop=0, optimize=True)
report = {
    'source_blend': BLEND,
    'frames': frames,
    'fps': 30,
    'gif': GIF,
    'frame_count': len(paths),
    'model_bones': len(arm.data.bones),
    'model_meshes': sum(1 for o in bpy.data.objects if o.type == 'MESH'),
    'action': arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
}
json.dump(report, open(os.path.join(OUT, 'Ellie_Patrol_ExactAnimationPreview_report.json'), 'w', encoding='utf-8'), indent=2)
print('EXACT_ANIMATION_PREVIEW', json.dumps(report))
