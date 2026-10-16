import bpy
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for ob in bpy.data.objects:
    if ob.type=='MESH' and any(m.type=='ARMATURE' and m.object==arm for m in ob.modifiers):ob.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx',use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.glb',export_format='GLB',use_selection=True,export_animations=False,export_all_influences=True)
