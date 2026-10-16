import bpy
import json,hashlib
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
source=ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene
scene.frame_set(1)
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'Exports/Ellie_Patrol_NeutralModel_Preview.png')
bpy.ops.render.render(write_still=True)
(ROOT/'Exports/Ellie_Patrol_NeutralModel_Preview_report.json').write_text(json.dumps({'blend':str(source),'png':scene.render.filepath,
    'source_blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest(),
    'stage_meshes':sum(o.type=='MESH' and o.name.startswith('Catalog_CapturedFG_') for o in scene.objects),
    'pose':'Original source bind mesh and declared1152joint export reference; no capture corrective or animation.'},indent=2))
