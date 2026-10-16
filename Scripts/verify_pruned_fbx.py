"""Open every pruned FBX in isolation and record armature/mesh counts."""
import bpy, os, json

root = r'D:/TLOU2_UE5_8_Codex/Exports/PrunedArmature'
out_path = r'D:/TLOU2_UE5_8_Codex/Exports/pruned_fbx_validation.json'
rows=[]
for fn in sorted(os.listdir(root)):
    if not fn.lower().endswith('.fbx'):
        continue
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    path=os.path.join(root,fn)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False, use_prepost_rot=True)
    arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    rows.append({
        'file':fn,
        'size_bytes':os.path.getsize(path),
        'armatures':len(arms),
        'armature_name':arms[0].name if arms else None,
        'first_bone':arms[0].data.bones[0].name if arms and arms[0].data.bones else None,
        'bones':len(arms[0].data.bones) if arms else 0,
        'meshes':len(meshes),
        'vertices':sum(len(o.data.vertices) for o in meshes),
        'vertex_groups':sorted(set(len(o.vertex_groups) for o in meshes)),
        'all_meshes_have_armature_modifier':all(any(m.type=='ARMATURE' for m in o.modifiers) for o in meshes),
    })
with open(out_path,'w') as f:
    json.dump(rows,f,indent=2)
print('PRUNED_FBX_VERIFY', json.dumps(rows), flush=True)
