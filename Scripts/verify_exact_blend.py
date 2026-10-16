import bpy, json

path=r'D:/TLOU2_UE5_8_Codex/Blender/Ellie_Patrol_Catalog_Exact.blend'
bpy.ops.wm.open_mainfile(filepath=path)
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
meshes=[o for o in bpy.data.objects if o.type=='MESH']
rows={'file':path,'objects':len(bpy.data.objects),'armatures':len(arms),
      'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),
      'actions':len(bpy.data.actions),'armature_name':arms[0].name if arms else None,
      'bones':len(arms[0].data.bones) if arms else 0,
      'mesh_armature_modifiers':sum(any(m.type=='ARMATURE' for m in o.modifiers) for o in meshes),
      'all_meshes_armature':all(any(m.type=='ARMATURE' for m in o.modifiers) for o in meshes)}
json.dump(rows,open(r'D:/TLOU2_UE5_8_Codex/Exports/exact_blend_validation.json','w'),indent=2)
print('EXACT_BLEND_VERIFY',json.dumps(rows))
