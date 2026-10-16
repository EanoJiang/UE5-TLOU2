"""Write a second FBX set with all 1074 source bones and pruned groups.

Some UE import paths require an FBX bone tree to exactly match the destination
skeleton.  This variant keeps the complete hierarchy while retaining the
per-mesh weight-group reduction of the normal pruned set.
"""
import bpy, os, json

ROOT=r'D:/TLOU2_UE5_8_Codex'
src_script=os.path.join(ROOT,'Scripts','make_pruned_armature_fbx.py')
ns={'__name__':'pruned_module'}
exec(compile(open(src_script,encoding='utf-8').read(),src_script,'exec'),ns)
ns['OUT_DIR']=os.path.join(ROOT,'Exports','FullBonePruned')
ns['KEEP_ALL_BONES']=True
os.makedirs(ns['OUT_DIR'],exist_ok=True)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.objects if o.type=='MESH']
chunks=ns['mesh_chunks'](meshes)
report={'source_blend':ns['SRC_BLEND'],'source_bone_count':len(arm.data.bones),'source_mesh_count':len(meshes),'chunks':{}}
for chunk,objs in chunks.items():
    print('FULLBONE_START',chunk,len(objs),flush=True)
    report['chunks'][chunk]=ns['clone_chunk'](chunk,objs,arm)
    print('FULLBONE_DONE',chunk,flush=True)
with open(os.path.join(ROOT,'Exports','fullbone_pruned_manifest.json'),'w') as f:
    json.dump(report,f,indent=2)
print('FULLBONE_MANIFEST',flush=True)
