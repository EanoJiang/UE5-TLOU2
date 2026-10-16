import bpy,os
from mathutils import Vector
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_Exact.blend')
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob.get('source_material') in ('patrol-tshirt','theater-pants','shoes','torso-ao'):
        ob.hide_render=True; ob.hide_viewport=True
sc=bpy.context.scene;sc.view_settings.exposure=-1.8
sc.render.engine='BLENDER_EEVEE_NEXT';sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
cam=sc.camera;cam.location=(1.7,-3.6,1.7);cam.data.lens=62
cam.rotation_euler=(Vector((0,0,1.00))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=ROOT+'/Exports/TextureDiagnostic/CaptureLayer_Full_1920.png';bpy.ops.render.render(write_still=True)
cam.location=(.65,-1.65,1.78);cam.data.lens=62;cam.rotation_euler=(Vector((0,0,1.47))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=ROOT+'/Exports/TextureDiagnostic/CaptureLayer_Head_1920.png';bpy.ops.render.render(write_still=True)
