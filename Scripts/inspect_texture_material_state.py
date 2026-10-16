import bpy,json
bpy.ops.wm.open_mainfile(filepath='D:/TLOU2_UE5_8_Codex/Blender/Ellie_Patrol_Catalog_Exact.blend')
for m in bpy.data.materials:
 if m.use_nodes:
  bs=m.node_tree.nodes.get('Principled BSDF')
  print('MAT',m.name,'BS',list(bs.inputs['Base Color'].default_value),[(l.from_node.name,l.from_socket.name) for l in bs.inputs['Base Color'].links], 'imgs',[(n.name,n.image.name,n.image.filepath,n.image.colorspace_settings.name,tuple(n.image.size)) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])
for o in bpy.data.objects:
 if o.type=='MESH':print('MESH',o.name,o.get('source_pak'),o.get('source_material'),[m.name for m in o.data.materials])
