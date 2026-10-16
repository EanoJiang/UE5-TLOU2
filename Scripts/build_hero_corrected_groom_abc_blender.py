import bpy,numpy as np,json,hashlib
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex');OUT=ROOT/'Exports/Groom';NPZ=OUT/'Ellie_Patrol_CaptureGroom_curves.npz';ABC=OUT/'Ellie_Patrol_CaptureGroom_HeroCorrected.abc';d=np.load(NPZ,allow_pickle=True);pos=d['positions_cm'];gid=d['group_ids'];width=d['widths_mm'].copy();srcobj=d['source_object_index'];srcisl=d['source_island_index'];groups=d['group_names'];hero_uv={16,66,78,90,119,195,199,200,201};hero=(gid==1)&(srcobj==5)&np.isin(srcisl,list(hero_uv));width[hero]=np.clip(width[hero]*1.75,.09,.14)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_CaptureGroom.blend'));sc=bpy.data.scenes.new('HeroCorrectedExport');bpy.context.window.scene=sc
for gi,g in enumerate(groups):
 sel=(gid==gi);points=pos[sel];ws=width[sel];data=bpy.data.curves.new('Groom_Ellie_'+str(g),'CURVE');data.dimensions='3D';data.resolution_u=1;data.bevel_resolution=0;data.bevel_depth=.0035
 for curve,w in zip(points,ws):
  p=data.splines.new('POLY');p.points.add(len(curve)-1);export=curve[:,[0,2,1]].copy();export[:,1]*=-1;co=np.column_stack((export,np.ones(len(export),np.float32)));p.points.foreach_set('co',co.ravel());rad=np.ones(len(export),np.float32)*(w*.05);rad[0]*=.7;rad[-8:]*=np.linspace(1,.08,8);p.points.foreach_set('radius',rad)
 obj=bpy.data.objects.new('Groom_Ellie_'+str(g),data);sc.collection.objects.link(obj);obj['groom_group_id']=gi;data['groom_group_id']=gi;data['groom_group_id_AbcGeomScope']='con';obj['hero_uv_ids']=','.join(map(str,sorted(hero_uv))) if gi==1 else ''
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.wm.alembic_export(filepath=str(ABC),start=1,end=1,xsamples=1,gsamples=1,selected=True,flatten=False,global_scale=1.,export_hair=False,export_particles=False,packuv=False,uvs=False,normals=False,vcolors=False,face_sets=False,curves_as_mesh=False,use_instancing=False,export_custom_properties=True,triangulate=False)
# The export above selected only last object; export all again by selecting all curve objects
bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects:o.select_set(True)
bpy.context.view_layer.objects.active=sc.objects[0]
bpy.ops.wm.alembic_export(filepath=str(ABC),start=1,end=1,xsamples=1,gsamples=1,selected=True,flatten=False,global_scale=1.,export_hair=False,export_particles=False,packuv=False,uvs=False,normals=False,vcolors=False,face_sets=False,curves_as_mesh=False,use_instancing=False,export_custom_properties=True,triangulate=False)
report={'pass':ABC.is_file(),'abc':str(ABC),'curve_count':int(len(pos)),'hero_curve_count':int(hero.sum()),'hero_uv_ids':sorted(hero_uv),'hero_width_mm_min_max':[float(width[hero].min()),float(width[hero].max())],'group_counts':{str(int(i)):int((gid==i).sum()) for i in range(4)},'sha256':hashlib.sha256(ABC.read_bytes()).hexdigest()};(OUT/'hero_corrected_groom_build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
