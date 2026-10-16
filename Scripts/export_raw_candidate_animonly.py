import bpy,os
ROOT=r'D:\TLOU2_UE5_8_Codex'; out=os.path.join(ROOT,'Exports','Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_AnimOnly.fbx')
bpy.ops.object.select_all(action='DESELECT'); arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=out,use_selection=True,object_types={'ARMATURE'},bake_anim=True,bake_anim_use_all_actions=False,add_leaf_bones=False,axis_forward='-Z',axis_up='Y')
print('EXPORTED',out)
