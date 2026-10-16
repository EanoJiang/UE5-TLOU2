import bpy, os, math
from mathutils import Vector
out=r'D:/TLOU2_UE5_8_Codex/Exports/Ellie_1074_SkeletonProbe.fbx'
# identify armature and save existing
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
# delete all meshes except create probe
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.data.objects):
    if o.type=='MESH': bpy.data.objects.remove(o, do_unlink=True)
# create a tiny triangle around origin, parent to armature and root weights
mesh=bpy.data.meshes.new('Ellie_1074_SkeletonProbeMesh')
mesh.from_pydata([(0,0,0),(10,0,0),(0,10,0)],[],[(0,1,2)]); mesh.update()
obj=bpy.data.objects.new('Ellie_1074_SkeletonProbe',mesh); bpy.context.collection.objects.link(obj)
obj.parent=arm
# assign vertex group to first/root bone if available
root=arm.data.bones[0]
vg=obj.vertex_groups.new(name=root.name); vg.add([0,1,2],1.0,'REPLACE')
mod=obj.modifiers.new('Armature','ARMATURE'); mod.object=arm
# select arm and mesh
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); obj.select_set(True); bpy.context.view_layer.objects.active=arm
# export
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'ARMATURE','MESH'}, add_leaf_bones=False, bake_anim=False, apply_unit_scale=True, axis_forward='-Z', axis_up='Y', use_armature_deform_only=False, mesh_smooth_type='FACE', use_custom_props=True, primary_bone_axis='Y', secondary_bone_axis='X')
print('EXPORTED',out,os.path.getsize(out),'bones',len(arm.data.bones))
# save separate blend
bpy.ops.wm.save_as_mainfile(filepath=r'D:/TLOU2_UE5_8_Codex/Blender/Ellie_1074_SkeletonProbe.blend')
