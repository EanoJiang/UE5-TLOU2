import bpy
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Catalog_Extracted'):
  o.scale=(.5,.5,.5);o.select_set(True)
bpy.ops.export_scene.fbx(filepath=ROOT+'/Exports/Catalog_Extracted_WetPlinth.fbx',use_selection=True,object_types={'MESH'},bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=ROOT+'/Exports/Catalog_Extracted_WetPlinth.glb',export_format='GLB',use_selection=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
bpy.context.scene.render.filepath=ROOT+'/Exports/Ellie_Patrol_CaptureMatched_Catalog_1920.png';bpy.ops.render.render(write_still=True)
