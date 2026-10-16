import bpy,csv,os
p=r'D:\TLOU2_UE5_8_Codex\Exports\Ellie_1074_RootMotion_AnimationProbe.fbx'; out=r'D:\TLOU2_UE5_8_Codex\Exports\Ellie_1074_RootMotion_AnimationProbe.csv'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=p,use_anim=True)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE'); a=arm.animation_data.action
scene=bpy.context.scene
with open(out,'w',newline='') as f:
 w=csv.writer(f);w.writerow(['frame','time_s','object_x','object_y','object_z','root_bone_x','root_bone_y','root_bone_z'])
 for fr in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
  scene.frame_set(fr); b=arm.pose.bones.get('root');
  w.writerow([fr,(fr-2)/30.0,arm.location.x,arm.location.y,arm.location.z,b.location.x if b else 0,b.location.y if b else 0,b.location.z if b else 0])
print(out)
