"""Replace the composite stand with all33 original captured FG subsets.

Original skin and graphics-instance matrices are baked into world positions.
No empirical scale or actor rotation is applied a second time. Character
geometry, armature, actions and frame are asserted unchanged.
"""
import bpy,json,sys,hashlib,shutil
from pathlib import Path
import numpy as np
ROOT=Path('D:/TLOU2_UE5_8_Codex')
SOURCE=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
RAW=ROOT/'Exports/CapturedFGStage/captured_fg_stage_manifest.json'
doc=json.loads(RAW.read_text())
TEXTURES=ROOT/'Exports/CapturedFGStage/TexturesDecoded'
texture_rows=json.loads((TEXTURES/'texture_decode_manifest.json').read_text())
texture_by_stem={Path(r['decoded_path']).stem:r for r in texture_rows}
assert doc['meshes']==33 and doc['bit_exact_bound_source_skin_subsets']==33

MAPS={
 'ped-wood-planks-a':('wood-floor-varnished-f-color','wood-floor-varnished-f-normal','wood-floor-varnished-f-roughness',None,None,None),
 'ped-wood-base-trim-a-plain':('wood-varnish-a-color','wood-varnish-a-normal','wood-varnish-a-roughness',None,None,None),
 'ped-dirt-grass-moss-a':('ground-seattle-pine-debries-a-color','ground-seattle-pine-debries-a-normal',None,None,None,None),
 'ped-asphalt-rubblepile-edge-b':('street-rubble-asphalt-large-a-color','street-rubble-asphalt-large-a-normal','street-rubble-asphalt-large-a-roughness',None,None,None),
 'ped-moss-cards-soft-a-wet':('moss-cards-a-soft-mix-color','moss-cards-a-soft-mix-normal','moss-cards-a-soft-mix-roughness',None,'moss-cards-a-soft-mix-opacity',None),
 'ped-moss-cards-soft-a':('moss-cards-a-soft-mix-color','moss-cards-a-soft-mix-normal','moss-cards-a-soft-mix-roughness',None,'moss-cards-a-soft-mix-opacity',None),
 'ped-floor-concrete-a':('concrete-mega-slab-a-alt-color','concrete-mega-slab-a-normal','concrete-mega-slab-a-roughness','concrete-mega-slab-a-ao',None,None),
 'shrub-fern-bracken-fg':('shrub-fern-bracken-color','shrub-fern-bracken-normal','shrub-fern-bracken-roughness',None,'shrub-fern-bracken-opacity-sdf',None),
 'ped-asphalt-rubblepile-edge-c':('street-rubble-asphalt-large-a-color','rubble-asphalt-large-a-normal','rubble-asphalt-large-a-roughness',None,None,None),
 'ped-wood-base-trim-a-dry':('wood-varnish-a-color','wood-varnish-a-normal','wood-varnish-a-roughness',None,None,None),
 'ped-ground-snow-a':('snow-smooth-mega-a-color','snow-icy-crunchy-normal','snow-icy-crunchy-roughness',None,None,None),
 'ped-wood-base-trim-a-snow':('wood-varnish-a-color','wood-varnish-a-normal','wood-varnish-a-roughness',None,None,None),
 'pedt-objects-icicles-a':(None,'default-flat-normal',None,None,None,None),
 'ped-jersey-barrier-concrete-a':('concrete-broken-a-color','concrete-broken-a-normal',None,None,None,None),
 'shrub-fern-bracken':('shrub-fern-bracken-color','shrub-fern-bracken-normal','shrub-fern-bracken-roughness',None,'shrub-fern-bracken-opacity-sdf',None),
 'ped-dept-store-carpet':('carpet-office-b-color','carpet-office-a-normal',None,'carpet-office-a-ao',None,None),
 'ped-gym-floor-wood-varnished-planks-worn':('wood-floor-varnished-f-color','wood-floor-varnished-f-normal','wood-floor-varnished-f-roughness',None,None,None),
 'ped-gym-floor-lines':(None,'default-flat-normal',None,None,None,None),
 'ped-leaves-single':('leaves-dead-a-color','leaves-dead-a-normal',None,'leaves-dead-a-ao',None,None),
 'ped-hos-linoleum-floor-swatch':('uth-lab-linoleum-floor-a-upres-color','default-flat-normal','uth-lab-linoleum-floor-a-upres-roughness',None,None,None),
 'ped-concret-rock-pile':('rubble-dust-pile-a-color','rubble-dust-pile-a-normal','rubble-dust-pile-a-roughness',None,None,None),
 'ped-concrete-damage':('concrete-pitted-a-color','concrete-pitted-a-normal',None,None,None,None),
 'aqu-wood-varnish-a':('wood-varnish-a-color','wood-varnish-a-normal','wood-varnish-a-roughness',None,None,None),
 'moss-cards-soft-a':('moss-cards-a-soft-mix-color','moss-cards-a-soft-mix-normal','moss-cards-a-soft-mix-roughness',None,'moss-cards-a-soft-mix-opacity',None),
 't2r-nor-mus-floor-trim-damage-dirt-grass':('nor-mus-trim-set-a-color','nor-mus-trim-set-a-normal',None,None,None,None),
 't2r-nor-mus-space-floor-pattern-broken-dust-moss-leaves':('t2r-nor-mus-space-floor-pattern-a-color','t2r-nor-mus-space-floor-pattern-a-normal',None,None,None,'t2r-nor-mus-space-floor-pattern-a-metallic'),
 'chair-dining-joels-house-a':('chair-dining-joels-house-a-color','chair-dining-joels-house-a-normal','chair-dining-joels-house-a-roughness',None,None,None),
}

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
def signature():
    meshes={o.name:len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)}
    return {'meshes':meshes,'bones':len(arm.data.bones),'action':arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
            'frame':bpy.context.scene.frame_current,'frame_start':bpy.context.scene.frame_start,'frame_end':bpy.context.scene.frame_end}
before=signature()
assert len(before['meshes'])==29 and sum(before['meshes'].values())==84954
removed=[]
for ob in list(bpy.data.objects):
    if ob.type=='MESH' and ob.name.startswith(('Catalog_Reconstructed','Catalog_Extracted','Catalog_CapturedFG')):
        removed.append(ob.name);data=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if data.users==0:bpy.data.meshes.remove(data)

made_materials={}
def material_for(key):
    if key in made_materials:return made_materials[key]
    name='M_FG_'+key
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Roughness'].default_value=.8
    bs.inputs['Base Color'].default_value=(.18,.18,.18,1)
    if key=='ped-gym-floor-lines':bs.inputs['Base Color'].default_value=(.75,.75,.7,1)
    if key=='pedt-objects-icicles-a':bs.inputs['Base Color'].default_value=(.75,.85,.88,1);bs.inputs['Roughness'].default_value=.12
    for channel,stem in zip(['color','normal','roughness','ao','opacity','metallic'],MAPS[key]):
        if not stem:continue
        row=texture_by_stem[stem];path=Path(row['decoded_path'])
        image=bpy.data.images.load(str(path),check_existing=True)
        image.colorspace_settings.name='sRGB' if channel=='color' else 'Non-Color'
        if not image.packed_file:image.pack()
        image.filepath=bpy.path.relpath(str(path),start=str(SOURCE.parent))
        node=nt.nodes.new('ShaderNodeTexImage');node.name='FG_'+channel;node.image=image
        mat['decoded_'+channel+'_texture']=str(path)
        if channel=='color':
            nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
        elif channel=='normal':
            normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
        elif channel=='roughness':nt.links.new(node.outputs['Color'],bs.inputs['Roughness'])
        elif channel=='metallic':nt.links.new(node.outputs['Color'],bs.inputs['Metallic'])
        elif channel=='opacity':
            mask=nt.nodes.new('ShaderNodeMath');mask.operation='GREATER_THAN';mask.inputs[1].default_value=.5
            nt.links.new(node.outputs['Color'],mask.inputs[0]);nt.links.new(mask.outputs[0],bs.inputs['Alpha'])
            mat.surface_render_method='DITHERED';mat.use_transparency_overlap=False
            mat['opacity_policy']='originaldepthprepassboundopacityR, clip.5 atcapturedgallerydistance; no inversion'
        # AO remains a separate source map for the UE material graph. Portable
        # Blender PBR does not silently bake it into the original base color.
    mat['source_pak']='keyart-turntable-fg.pak'
    mat['source_material']=key
    mat['shader_policy']='Original FG source maps through portable PBR; source layered/UV/detail shader constants remain separate evidence'
    made_materials[key]=mat
    return mat

objects=[];rows=[];maximum_error=0
for i,row in enumerate(doc['rows']):
    assert row.get('world_posed_npz'),('originalgraphicsinstanceworldnotready',i)
    z=np.load(row['world_posed_npz'])
    verts=z['posed_world_positions_blender_meters']
    indices=z['indices_raw'].view('<u2')[:row['count']].reshape(-1,3)
    name=f'Catalog_CapturedFG_{i:02d}_'+row['name'][:38]
    mesh=bpy.data.meshes.new('FG_'+row['name'][:55]);mesh.from_pydata(verts.tolist(),[],indices.tolist());mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material_for(row['material']))
    for polygon in mesh.polygons:polygon.use_smooth=True
    for key,binding in row['bindings'].items():
        if not key.startswith('uv') or key+'_raw' not in z:continue
        uv=z[key+'_raw'].view('<f2' if binding['type']==1 else '<f4').reshape(-1,2)
        layer=mesh.uv_layers.new(name='UVMap' if key=='uv0' else key.upper())
        for loop in mesh.loops:
            u,v=uv[loop.vertex_index];layer.data[loop.index].uv=(float(u),1-float(v))
    ob['source_pak']='keyart-turntable-fg.pak';ob['source_submesh']=row['name'];ob['source_material']=row['material']
    ob['capture_stage_index']=i;ob['capture_pose_policy']='originalcapturedskin then actualgraphicsinstanceworld; identityactor; noempiricalscale'
    error=max(abs(float(ob.data.vertices[j].co[k])-float(verts[j,k])) for j in range(len(verts)) for k in range(3))
    maximum_error=max(maximum_error,error)
    objects.append(ob)
    rows.append({'index':i,'object':ob.name,'source_submesh':row['name'],'source_pak':'keyart-turntable-fg.pak',
                 'material':row['material'],'blender_material':ob.data.materials[0].name,'vertices':len(verts),'indices':int(row['count']),
                 'world_posed_npz':row['world_posed_npz'],'blender_vertex_max_error_m':error})
assert len(objects)==33 and sum(r['vertices'] for r in rows)==101538
assert before==signature(),('characterchanged',before,signature())
scene=bpy.context.scene;scene['plinth_status']='originalFG33capturedskin+actualinstanceworld; priorcompositewet/concrete superseded'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
fbx=ROOT/'Exports/Catalog_CapturedFGStage.fbx';glb=ROOT/'Exports/Catalog_CapturedFGStage.glb'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False)
stage_scene=bpy.data.scenes.new('CapturedFGStage_Source');stage_scene.world=scene.world
for ob in objects:stage_scene.collection.objects.link(ob)
stage_blend=ROOT/'Blender/Catalog_CapturedFGStage.blend'
bpy.data.libraries.write(str(stage_blend),{stage_scene},path_remap='RELATIVE_ALL',fake_user=True)
source_pak=Path('D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/keyart-turntable-fg.pak')
pak_copy=ROOT/'Content/TLOU2/SourcePaks/keyart-turntable-fg.pak'
if not pak_copy.exists():shutil.copy2(source_pak,pak_copy)
manifest={'schema':'tlou2.captured_fg_stage_export.v1','source_pak':str(pak_copy),'source_evidence':str(RAW),
          'meshes':33,'vertices':101538,'materials':len(made_materials),'rows':rows,'material_maps':MAPS,
          'material_mapping_policy':'OriginalFGtexturecollection; portablePBR semanticselection. Activeconcreteslab andfern maps selectedfromoriginalsource; complexlayeredsourceconstantsnotfullyported.',
          'matrix_policy':'worldbakedfromoriginalskinpalette16andactualgraphicsinstanceworld; importidentityactor/scale1',
          'source_blend_updated':str(SOURCE),'character_signature_unchanged':before==signature(),
          'exports':{'fbx':str(fbx),'glb':str(glb),'blend':str(stage_blend)},
          'canonical_artifacts':[str(fbx),str(glb),str(stage_blend),str(pak_copy),str(RAW),str(TEXTURES/'texture_decode_manifest.json')],
          'supersedes':'Catalog_Extracted_WetPlinth composite and sourcewet-large/concrete-large stage; sourcecharacter29/1152unchanged'}
(ROOT/'Exports/capture_fg_stage_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
validation={'pass':maximum_error<1e-6 and before==signature(),'source_manifest':str(RAW),'export_manifest':str(ROOT/'Exports/capture_fg_stage_manifest.json'),
            'stage_meshes':33,'stage_vertices':101538,'source_skin_subsets_bit_exact':doc['bit_exact_bound_source_skin_subsets'],
            'blender_vertex_max_error_m':maximum_error,'character_unchanged':before==signature(),
            'scope':'WorldposedNPZtoBlenderpositions and originalindexcount; sourceGPUskin/index/instanceproof is separate. Doesnotclaim exactsourcepixelshader/UEstaticmeshvertexQA.'}
(ROOT/'Exports/capture_fg_stage_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print('CAPTURED_FG_STAGE_BUILT',SOURCE,len(objects),len(made_materials),maximum_error,before==signature())
