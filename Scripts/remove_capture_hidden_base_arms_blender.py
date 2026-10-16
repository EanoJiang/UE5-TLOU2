import bpy,json
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
arms=[o for o in bpy.data.objects if o.type=='MESH' and str(o.get('source_submesh','')).startswith('ellie16_patrol_hands')]
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for ob in arms:ob.select_set(True)
if arms:
    bpy.ops.export_scene.fbx(filepath=ROOT+'/Exports/Optional_BaseArms_Source.fbx',use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
rows=[{'object':o.name,'vertices':len(o.data.vertices),'source_submesh':o.get('source_submesh'),'source_pak':o.get('source_pak')} for o in arms]
for ob in arms:bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
json.dump({'removed_hidden_base_arms':rows,'reason':'Absent from captured GPU draws; jacket and gloves are the visible outfit','optional_source_fbx':ROOT+'/Exports/Optional_BaseArms_Source.fbx'},open(ROOT+'/Exports/capture_hidden_base_arms_report.json','w'),indent=2)
print('CAPTURE_BASE_ARMS_REMOVED',rows)
