import bpy, os
out=r'D:/TLOU2_UE5_8_Codex/Exports/Ellie_1074_RootMotion_Animation.fbx'
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
# remove meshes; FBX animation export can be armature-only
for o in list(bpy.data.objects):
 if o.type=='MESH': bpy.data.objects.remove(o,do_unlink=True)
bpy.context.scene.frame_start=1; bpy.context.scene.frame_end=80; bpy.context.scene.render.fps=30
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=out,use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_step=1.0,bake_anim_simplify_factor=0.0,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',use_custom_props=True)
print('EXPORTED_ANIM',out,os.path.getsize(out),len(arm.data.bones))
