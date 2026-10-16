import bpy,json,shutil
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
SOURCE=ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
ARCHIVE=ROOT/'Blender/Ellie_Patrol_PropBackpack1390_LegacyDebug.blend'
if not ARCHIVE.exists():shutil.copy2(SOURCE,ARCHIVE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
removed=[]
for ob in list(bpy.data.objects):
    if ob.type=='MESH' and ob.get('source_pak') in ('backpack-ellie.pak','ellie16-backpack.pak','ellie-backpack.pak'):
        removed.append({'name':ob.name,'vertices':len(ob.data.vertices),'source_material':ob.get('source_material')})
        bpy.data.objects.remove(ob,do_unlink=True)
ns={'__name__':'verified_backpack_mesh_build'}
path=ROOT/'Blender/build_full_patrol.py'
exec(compile(path.read_text().split('clear_scene();')[0],str(path),'exec'),ns)
ns['CAP_ROOT']=str(ROOT/'Exports/BackpackVariantDebug')
meta=json.loads((ROOT/'Exports/BackpackVariantDebug/ellie_backpack/capture.json').read_text())
made=[]
for item in meta['meshes']:
    ob=ns['build_mesh'](item,'ellie_backpack',arm,meta)
    for p in ob.data.polygons:p.use_smooth=True
    ob['joint_hierarchy_owner']='human'
    ob['capture_variant_verification']='ellie-backpack.pak; captured GPU bound mainhuman1074; original permesh vertexcounts 32/8184/3559/1454/94'
    made.append({'name':ob.name,'vertices':len(ob.data.vertices),'source_material':ob.get('source_material')})
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
out={'removed_wrong_prop_package':'backpack-ellie.pak','removed_meshes':removed,
     'replacement_package':'ellie-backpack.pak','replacement_meshes':made,
     'legacy_debug_blend':str(ARCHIVE),'main_rig_policy':'human1074 plus hoodie78; prop238 not part of selected outfit'}
(ROOT/'Exports/backpack_variant_replacement_report.json').write_text(json.dumps(out,indent=2))
print('BACKPACK_VARIANT_REPLACED',json.dumps(out))
