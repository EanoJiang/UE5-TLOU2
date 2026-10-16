import bpy
import json,hashlib
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(r"D:/TLOU2_UE5_8_Codex")
SOURCE=ROOT/"Blender/Ellie_Patrol_Original_0FW.blend"
OUT=ROOT/"Exports/Original0FWPreviewFrames"
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
scene.render.resolution_x=960
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
picks=list(range(1,81))
paths=[]
for frame in picks:
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/f"frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    paths.append(scene.render.filepath)
images=[Image.open(p).convert("RGB") for p in paths]
for frame,image in zip(picks,images):
    draw=ImageDraw.Draw(image)
    draw.rectangle((12,12,510,40),fill=(10,10,10))
    draw.text((20,20),f"Original 0FW right-arm layer | frame {frame}/80 | 30 fps",fill=(235,235,235))
gif=ROOT/"Exports/Ellie_Patrol_Original0FW_AnimationPreview.gif"
# GIF stores centiseconds; distribute 30/40ms samples to preserve source timing.
durations=[10*(round((i+1)*100/30)-round(i*100/30)) for i in range(len(images))]
images[0].save(gif,save_all=True,append_images=images[1:],duration=durations,loop=0,optimize=True)
still=ROOT/"Exports/Ellie_Patrol_Original0FW_Preview.png"
Image.open(paths[0]).save(still)
report={"source_blend":str(SOURCE),"gif":str(gif),"png":str(still),"source_frames":80,"source_rate_hz":30,"rendered_frames":picks,"frame_durations_ms":durations,"gif_duration_ms":sum(durations),"role":"decoded original sparse right-arm/finger clip on corrected reference pose; all80source samples rendered; model viewer base clip remains separate"}
report.update({'source_blend_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(still.read_bytes()).hexdigest(),
               'gif_sha256':hashlib.sha256(gif.read_bytes()).hexdigest(),'stage_meshes':sum(o.type=='MESH' and o.name.startswith('Catalog_CapturedFG_') for o in scene.objects)})
(ROOT/"Exports/Ellie_Patrol_Original0FW_AnimationPreview_report.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report))
