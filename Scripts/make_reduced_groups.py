import bpy, os, json
outfbx=r'D:/TLOU2_UE5_8_Codex/Exports/Ellie_Patrol_Catalog_ReducedGroups.fbx'
outblend=r'D:/TLOU2_UE5_8_Codex/Blender/Ellie_Patrol_Catalog_ReducedGroups.blend'
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
summary={}
for o in list(bpy.data.objects):
 if o.type!='MESH': continue
 used=set()
 for v in o.data.vertices:
  for g in v.groups:
   if g.weight>1e-8: used.add(o.vertex_groups[g.group].name)
 before=len(o.vertex_groups)
 # remove groups with no nonzero weights; iterate copy
 for vg in list(o.vertex_groups):
  if vg.name not in used: o.vertex_groups.remove(vg)
 summary[o.name]={'before':before,'after':len(o.vertex_groups),'used':len(used),'verts':len(o.data.vertices)}
# select all armature + meshes
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active=arm
for o in bpy.data.objects:
 if o.type=='MESH': o.select_set(True)
bpy.ops.export_scene.fbx(filepath=outfbx,use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',use_armature_deform_only=False,mesh_smooth_type='FACE',use_custom_props=True,primary_bone_axis='Y',secondary_bone_axis='X')
with open(r'D:/TLOU2_UE5_8_Codex/Exports/reduced_groups_summary.json','w') as f: json.dump(summary,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=outblend)
print('REDUCED',outfbx,os.path.getsize(outfbx), 'arm bones',len(arm.data.bones), 'meshes',len(summary))
