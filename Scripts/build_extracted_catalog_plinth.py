import bpy,os,json
from mathutils import Vector
ROOT='D:/TLOU2_UE5_8_Codex'
bpy.ops.wm.open_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
for ob in list(bpy.data.objects):
    if ob.type=='MESH' and ob.name.startswith(('Catalog_Reconstructed','Catalog_Extracted')):bpy.data.objects.remove(ob,do_unlink=True)
ns={'__name__':'mesh_build'};code=open(ROOT+'/Blender/build_full_patrol.py').read().split('clear_scene();')[0];exec(compile(code,ROOT+'/Blender/build_full_patrol.py','exec'),ns)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
made=[]
for folder in ['keyart_turntable_wet_large','keyart_turntable_fg','keyart_turntable_concrete_large']:
    meta=json.load(open(ROOT+'/Exports/ExactDebug/'+folder+'/capture.json'));meta['bones']=[]
    for item in meta['meshes']:
        if folder.endswith('_fg') and item['material'] not in ('shrub-fern-bracken','shrub-fern-bracken-fg'):continue
        if folder.endswith('concrete_large') and not (item['material']=='moss-cards-soft-a' or item['name'].startswith('leaves1')):continue
        ob=ns['build_mesh'](item,folder,arm,meta);ob.name='Catalog_Extracted_'+ob.name
        for mod in list(ob.modifiers):ob.modifiers.remove(mod)
        for p in ob.data.polygons:p.use_smooth=True
        ob.scale=(.5,.5,.5)
        if folder.endswith('_fg'):ob.location.z=.1357318115234375*.5
        made.append(ob)
textures={}
for r in json.load(open(ROOT+'/Exports/PlinthTexturesDecoded/texture_decode_manifest.json')):textures.setdefault(os.path.splitext(r['name'])[0],r['decoded_path'])
maps={
 'ped-moss-cards-soft-a-wet':('moss-cards-a-soft-mix-color','moss-cards-a-soft-mix-normal','moss-cards-a-soft-mix-opacity'),
 'ped-asphalt-rubblepile-edge-b':('street-rubble-asphalt-large-a-color','street-rubble-asphalt-large-a-normal',None),
 'ped-dirt-grass-moss-a':('ground-seattle-pine-debries-a-color','ground-seattle-pine-debries-a-normal',None),
 'ped-wood-base-trim-a':('wood-varnish-a-color','wood-varnish-a-normal',None),
 'shrub-fern-bracken':('shrub-fern-bracken-color','shrub-fern-bracken-normal','shrub-fern-bracken-opacity-sdf'),
 'shrub-fern-bracken-fg':('shrub-fern-bracken-color','shrub-fern-bracken-normal','shrub-fern-bracken-opacity-sdf'),
 'moss-cards-soft-a':('moss-cards-a-soft-mix-color','moss-cards-a-soft-mix-normal','moss-cards-a-soft-mix-opacity'),
 'ped-moss-cards-soft-a':('moss-cards-a-soft-mix-color','moss-cards-a-soft-mix-normal','moss-cards-a-soft-mix-opacity'),
}
rows=[]
for ob in made:
    key=ob.get('source_material');m=ob.data.materials[0];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.78
    color,normal,opacity=maps[key]
    for channel,stem in [('color',color),('normal',normal),('opacity',opacity)]:
        if not stem:continue
        img=bpy.data.images.load(textures[stem],check_existing=True);img.colorspace_settings.name='sRGB' if channel=='color' else 'Non-Color';node=nt.nodes.new('ShaderNodeTexImage');node.name='ND_Plinth_'+channel;node.image=img
        if channel=='color':nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
        elif channel=='normal':
            nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        else:
            nt.links.new(node.outputs['Color'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_transparency_overlap=False
        m['decoded_'+channel+'_texture']=textures[stem]
    rows.append({'object':ob.name,'source_pak':ob.get('source_pak'),'source_material':key,'vertices':len(ob.data.vertices)})
sc=bpy.context.scene;sc['plinth_status']='extracted original keyart-turntable-wet-large + shrub fern from keyart-turntable-fg'
bpy.ops.object.select_all(action='DESELECT')
for ob in made:ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=ROOT+'/Exports/Catalog_Extracted_WetPlinth.fbx',use_selection=True,object_types={'MESH'},bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=ROOT+'/Exports/Catalog_Extracted_WetPlinth.glb',export_format='GLB',use_selection=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend')
sc.render.filepath=ROOT+'/Exports/Ellie_Patrol_CaptureMatched_Catalog_1920.png';bpy.ops.render.render(write_still=True)
json.dump({'meshes':rows,'material_maps':maps},open(ROOT+'/Exports/extracted_catalog_plinth_manifest.json','w'),indent=2)
print('EXTRACTED_CATALOG_PLINTH',len(made))
