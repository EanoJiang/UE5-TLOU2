import bpy,os
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
# The extracted plinth is exported by build_extracted_catalog_plinth.py.
# Keep only meshes actually deformed by the combined character armature.
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
for ob in list(bpy.data.objects):
 if ob.type=='MESH' and not any(m.type=='ARMATURE' and m.object==arm for m in ob.modifiers):bpy.data.objects.remove(ob,do_unlink=True)
ns={'__name__':'capture_chunk_export'};exec(compile(open(ROOT+'/Scripts/make_pruned_armature_fbx.py').read(),ROOT+'/Scripts/make_pruned_armature_fbx.py','exec'),ns)
ns['SRC_BLEND']=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend';ns['OUT_DIR']=ROOT+'/Exports/CaptureMatchedChunks';ns['MANIFEST']=ROOT+'/Exports/capture_matched_chunk_manifest.json';os.makedirs(ns['OUT_DIR'],exist_ok=True);ns['main']()
