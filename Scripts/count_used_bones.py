import bpy, json
out={}
for o in bpy.data.objects:
 if o.type!='MESH': continue
 used=set()
 for v in o.data.vertices:
  for g in v.groups:
   if g.weight>1e-7: used.add(o.vertex_groups[g.group].name)
 out[o.name]={'verts':len(o.data.vertices),'groups':len(o.vertex_groups),'used_bones':len(used),'bones':sorted(used)}
open('D:/TLOU2_UE5_8_Codex/Exports/mesh_used_bones.json','w').write(json.dumps(out,indent=2))
