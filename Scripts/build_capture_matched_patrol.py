import bpy, os, json, math, random
from mathutils import Vector
ROOT='D:/TLOU2_UE5_8_Codex'
SRC=ROOT+'/Blender/Ellie_Patrol_Catalog_Exact.blend'
OUT=ROOT+'/Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
bpy.ops.wm.open_mainfile(filepath=SRC)
removed=[]
for ob in list(bpy.data.objects):
    if ob.type=='MESH' and ob.get('source_material') in ('patrol-tshirt','theater-pants','shoes','torso-ao'):
        removed.append({'object':ob.name,'source_material':ob.get('source_material'),'source_pak':ob.get('source_pak')})
        bpy.data.objects.remove(ob,do_unlink=True)
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.data.objects if o.type=='MESH']
# Correct neutral skin normal Z for portable material consumers.
head=bpy.data.materials.get('M_ND_head')
if head:
    nt=head.node_tree;node=nt.nodes.get('ND_Normal_head');nm=nt.nodes.get('ND_NormalMap_head')
    if node and nm:
        img=bpy.data.images.load(ROOT+'/Exports/TexturesDecoded/ellie-head-normal-xyz.png',check_existing=True);img.colorspace_settings.name='Non-Color';node.image=img
        nt.links.new(node.outputs['Color'],nm.inputs['Color']);head['decoded_normal_texture']=img.filepath

# Hair's default dielectric lobe was too broad for the strand cards. Keep a
# restrained rough fibre response until the captured anisotropic shader is ported.
for m in bpy.data.materials:
    if m.name.startswith('M_ND_hair') and m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9;bs.inputs['Specular IOR Level'].default_value=.16

sc=bpy.context.scene;sc.frame_set(1);sc.render.engine='BLENDER_EEVEE_NEXT'
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.view_settings.exposure=-1.45
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.025,.025,.025,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.2
cam=sc.camera;cam.location=(2.45,-5.6,2.0);cam.data.lens=50;cam.rotation_euler=(Vector((0,0,.9))-cam.location).to_track_quat('-Z','Y').to_euler()

# Export character geometry before adding the reconstructed scene plinth.
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm
fbx=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx';glb=ROOT+'/Exports/Ellie_Patrol_Catalog_CaptureMatched.glb'
bpy.ops.export_scene.fbx(filepath=fbx,use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True,export_animations=False)

def simplemat(name,color,rough=.9):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;return m
stone=simplemat('M_Catalog_Plinth_Earth',(.075,.065,.044));nt=stone.node_tree;bs=nt.nodes.get('Principled BSDF')
noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=18;noise.inputs['Detail'].default_value=4
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.025,.024,.018,1);ramp.color_ramp.elements[1].color=(.12,.11,.08,1);nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs['Base Color'])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.5;bump.inputs['Distance'].default_value=.015;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],bs.inputs['Normal'])
wood=simplemat('M_Catalog_Plinth_Rim',(.05,.025,.012),.5)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.77,depth=.12,location=(0,0,-.095));rim=bpy.context.object;rim.name='Catalog_Reconstructed_Round_Rim';rim.data.materials.append(wood)
bevel=rim.modifiers.new('Round edge','BEVEL');bevel.width=.012;bevel.segments=3
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.75,depth=.055,location=(0,0,-.0225));soil=bpy.context.object;soil.name='Catalog_Reconstructed_Earth_Top';soil.data.materials.append(stone)
grassm=[simplemat('M_Catalog_Grass_'+str(i),c) for i,c in enumerate([(.055,.085,.018),(.11,.13,.035),(.07,.105,.025)])]
random.seed(97);verts=[];faces=[]
for i in range(1800):
    x=random.uniform(-.7,.7);y=random.uniform(-.7,.7)
    if x*x+y*y>.49 or (abs(x)<.19 and -.23<y<.2):continue
    # Sparse grass on the earth top; the capture has a worn clear centre.
    if math.hypot(x,y)<.34 and random.random()<.9:continue
    z=.009;h=random.uniform(.012,.05);w=random.uniform(.002,.006);dx=random.uniform(-.02,.02);dy=random.uniform(-.02,.02);n=len(verts)
    verts.extend([(x-w,y,z),(x+w,y,z),(x+dx,y+dy,z+h)]);faces.append((n,n+1,n+2))
me=bpy.data.meshes.new('Catalog_Grass_Patch');me.from_pydata(verts,[],faces);ob=bpy.data.objects.new('Catalog_Reconstructed_Grass',me);bpy.context.collection.objects.link(ob)
for m in grassm:me.materials.append(m)
for p in me.polygons:p.material_index=random.randrange(3)

sc['capture_visible_mesh_count']=len(meshes);sc['hidden_duplicate_source_layers']=json.dumps(removed);sc['plinth_status']='reconstructed 3D presentation surface, not an extracted capture mesh'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
sc.render.filepath=ROOT+'/Exports/Ellie_Patrol_CaptureMatched_Catalog_1920.png';bpy.ops.render.render(write_still=True)
cam.location=(.65,-1.65,1.78);cam.data.lens=62;cam.rotation_euler=(Vector((0,0,1.47))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=ROOT+'/Exports/Ellie_Patrol_CaptureMatched_Head_1920.png';bpy.ops.render.render(write_still=True)
report={'source_blend':SRC,'blend':OUT,'fbx':fbx,'glb':glb,'character_mesh_count':len(meshes),'bones':len(arm.data.bones),'vertices':sum(len(o.data.vertices) for o in meshes),'removed_duplicate_layers':removed,'plinth':'reconstructed 3D'}
json.dump(report,open(ROOT+'/Exports/capture_matched_patrol_manifest.json','w'),indent=2)
print('CAPTURE_MATCHED_PATROL',report)
