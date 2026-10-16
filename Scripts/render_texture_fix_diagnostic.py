import bpy, os, json
from mathutils import Vector
ROOT = "D:/TLOU2_UE5_8_Codex"
bpy.ops.wm.open_mainfile(filepath=ROOT + "/Blender/Ellie_Patrol_Catalog_Exact.blend")
for image in bpy.data.images:
    if image.source == 'FILE':
        try: image.reload()
        except Exception: pass
for mat in bpy.data.materials:
    if not mat.use_nodes: continue
    bs = mat.node_tree.nodes.get('Principled BSDF')
    if bs:
        for link in list(bs.inputs['Normal'].links): mat.node_tree.links.remove(link)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'
sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.frame_set(1)
sc.render.filepath=ROOT+'/Exports/TextureDiagnostic/HighRes_ColorOnly_Full.png'
bpy.ops.render.render(write_still=True)
cam=sc.camera;cam.location=(.8,-1.8,1.8);cam.data.lens=65
cam.rotation_euler=(Vector((0,0,1.48))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=ROOT+'/Exports/TextureDiagnostic/HighRes_ColorOnly_Head.png'
bpy.ops.render.render(write_still=True)
print('TEXTURE_FIX_DIAGNOSTIC_DONE')
