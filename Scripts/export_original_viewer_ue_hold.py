import bpy,json
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie16_Patrol_OriginalViewerPose.blend')
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;sc.frame_set(1);sc.frame_end=2
for pb in arm.pose.bones:
    for p in ['location','rotation_quaternion','scale']:pb.keyframe_insert(p,frame=2,group=pb.name)
arm.animation_data.action['ue_import_compatibility']='Two identical pose samples because UE5.8 FBX bake rejects a zero-length range; source pose remains one frame.'
me=bpy.data.meshes.new('OriginalViewerPose_UEHoldCarrier');me.from_pydata([(0,0,0),(.01,0,0),(0,.01,0)],[],[(0,1,2)]);ob=bpy.data.objects.new('OriginalViewerPose_UEHoldCarrier',me);bpy.context.collection.objects.link(ob);vg=ob.vertex_groups.new(name='root');vg.add([0,1,2],1,'REPLACE');ob.modifiers.new('Armature','ARMATURE').object=arm
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=arm
out=ROOT+'/Exports/Ellie16_Patrol_OriginalViewerPose_UEHoldCarrier.fbx'
bpy.ops.export_scene.fbx(filepath=out,use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',use_custom_props=True)
json.dump({'source_pose_frames':1,'ue_carrier_samples':2,'same_static_pose':True,'source_clip':'model-viewer-ellie-16-patrol','carrier':out},open(ROOT+'/Exports/original_viewer_ue_hold_metadata.json','w'),indent=2)
