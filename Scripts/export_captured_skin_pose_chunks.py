import bpy,os
from mathutils import Matrix
ROOT='D:/TLOU2_UE5_8_Codex'
SOURCE=ROOT+'/Blender/Ellie_Patrol_CapturedSkinPose.blend'
bpy.ops.wm.open_mainfile(filepath=SOURCE)
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
arm.animation_data_clear()
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for ob in list(bpy.data.objects):
    if ob.type=='MESH' and not any(m.type=='ARMATURE' and m.object==arm for m in ob.modifiers):
        bpy.data.objects.remove(ob,do_unlink=True)
    elif ob.type=='MESH' and ob.data.shape_keys:
        for key in ob.data.shape_keys.key_blocks:
            if key.name!='Basis':key.value=0
bpy.context.view_layer.update()
ns={'__name__':'capture_pose_chunks'}
path=ROOT+'/Scripts/make_pruned_armature_fbx.py'
exec(compile(open(path).read(),path,'exec'),ns)
ns['SRC_BLEND']=SOURCE
ns['OUT_DIR']=ROOT+'/Exports/CapturedSkinPoseChunks'
ns['MANIFEST']=ROOT+'/Exports/captured_skin_pose_chunk_manifest.json'
os.makedirs(ns['OUT_DIR'],exist_ok=True)
ns['main']()
