import bpy
import json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector

ROOT=Path('D:/TLOU2_UE5_8_Codex')
source=ROOT/'Blender/Ellie_Patrol_CapturedSkinPose.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene
scene.frame_set(1)
palette=json.loads((ROOT/'Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.json').read_text())
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.matrix_world=Matrix(palette['actor_world_blender'])
scene.camera.location=(0,-3,1.15)
forward=Vector((2.60973e-6,.983470887,-.181064765))
scene.camera.rotation_euler=forward.to_track_quat('-Z','Y').to_euler()
scene.camera.data.sensor_fit='HORIZONTAL'
scene.camera.data.sensor_width=36
scene.camera.data.lens=36/(2*math.tan(math.radians(79.9908974)/2))
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'Exports/Ellie_Patrol_CapturedSkinPose_Preview.png')
bpy.ops.render.render(write_still=True)
report={'blend':str(source),'png':scene.render.filepath,'render_engine':scene.render.engine,
        'source_blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest(),
        'stage_meshes':sum(o.type=='MESH' and o.name.startswith('Catalog_CapturedFG_') for o in scene.objects),
        'source_frames':1,'pose':'Captured skin palettes with explicit affine-to-TRS vertex corrective',
        'camera':'Captured camera(0,1.15,3)gameY-up, horizontalFOV79.9908974deg; original actorWorld applied for rendering.',
        'note':'Blender preview; final UE runtime screenshot is delivered separately.'}
(ROOT/'Exports/Ellie_Patrol_CapturedSkinPose_Preview_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
