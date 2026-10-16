import bpy,json,os
from mathutils import Matrix,Vector
ROOT='D:/TLOU2_UE5_8_Codex'
BLEND=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
REST=ROOT+'/Exports/Ellie_CorrectBindRest_SourceMatrices.json'
bpy.ops.wm.open_mainfile(filepath=BLEND)
doc=json.load(open(REST));rows=doc['rows'];arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.animation_data_clear();arm.location=(0,0,0);arm.rotation_euler=(0,0,0);arm.scale=(1,1,1)
bpy.context.view_layer.objects.active=arm;bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for r in rows:
    eb=arm.data.edit_bones.get(r['bone_name'])
    if not eb:raise RuntimeError('missingbone '+r['bone_name'])
    mat=Matrix(r['global_matrix_blender_meters'])
    eb.matrix=mat;eb.length=.025;eb.use_connect=False
for r in rows:
    eb=arm.data.edit_bones[r['bone_name']];p=r['parent_index'];eb.parent=arm.data.edit_bones[rows[p]['bone_name']] if p>=0 else None
bpy.ops.object.mode_set(mode='OBJECT')
for pb in arm.pose.bones:
    pb.matrix_basis=Matrix.Identity(4)
arm['bind_rest_source']=REST;arm['bind_rest_units']='meters';arm['source_sqt_bones']=520;arm['procedural_helper_identity_fallback']=554
character=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('Catalog_Reconstructed')]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in character:o.select_set(True)
bpy.ops.export_scene.fbx(filepath=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx',use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.glb',export_format='GLB',use_selection=True,export_animations=False)
# Small carrier imports all1074 correctrestbones first; it is excluded from the
# final catalog map and exists only to establish the canonical shared skeleton.
bpy.ops.object.select_all(action='DESELECT')
me=bpy.data.meshes.new('CaptureMatched_SkeletonCarrierMesh');me.from_pydata([(0,0,0),(.001,0,0),(0,.001,0)],[],[(0,1,2)]);ob=bpy.data.objects.new('CaptureMatched_SkeletonCarrier',me);bpy.context.collection.objects.link(ob)
vg=ob.vertex_groups.new(name='root');vg.add([0,1,2],1,'REPLACE');mod=ob.modifiers.new('ArmatureDeform','ARMATURE');mod.object=arm
ob.select_set(True);arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=ROOT+'/Exports/Ellie_CaptureMatched1074_SkeletonCarrier.fbx',use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True,use_armature_deform_only=False)
bpy.data.objects.remove(ob,do_unlink=True)
report={'blend':BLEND,'armature':arm.name,'bones':len(arm.data.bones),'source_sqt_bones':520,'helper_fallback_bones':554,'root_head':list(arm.data.bones['root'].head_local),'head_height':max(b.head_local.z for b in arm.data.bones),'mesh_count':len(character)}
json.dump(report,open(ROOT+'/Exports/capture_matched_correct_bind_rest.json','w'),indent=2);print('CORRECT_CAPTURE_MATCHED_REST',report)
