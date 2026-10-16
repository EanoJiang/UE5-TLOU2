import bpy, os
from mathutils import Vector

ROOT=r'D:/TLOU2_UE5_8_Codex'
BLEND=ROOT+'/Blender/Ellie_Patrol_RawRootCandidate_90LFW.blend'
OUT=ROOT+'/Exports/RawRootCandidatePreviewFrames'
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=512
scene.render.resolution_y=512
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
os.makedirs(OUT,exist_ok=True)
if not scene.camera:
    bpy.ops.object.camera_add(location=(2.6,-4.6,2.0))
    scene.camera=bpy.context.object
scene.camera.location=(2.6,-4.6,2.0)
scene.camera.rotation_euler=(Vector((0,0,1.0))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
n=scene.frame_end
picks=sorted(set([1,max(1,n//4),max(1,n//2),max(1,(3*n)//4),n]))
for frame in picks:
    scene.frame_set(frame)
    scene.render.filepath=os.path.join(OUT,f'frame_{frame:04d}.png')
    bpy.ops.render.render(write_still=True)
print('RAW_ROOT_FRAMES',picks)
