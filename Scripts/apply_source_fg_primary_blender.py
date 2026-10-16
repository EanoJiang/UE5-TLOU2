"""Port capture-proven FG primary tint/wet math; keep every object/face/action."""
import bpy,json,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path('D:/TLOU2_UE5_8_Codex')
SOURCE=Path(sys.argv[sys.argv.index('--')+1])
DECODED=ROOT/'Exports/CapturedFGStage/TexturesDecoded'
DERIVED=ROOT/'Exports/CapturedFGStage/TexturesDerived';DERIVED.mkdir(exist_ok=True)

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def srgb(linear):return np.where(linear<=.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055)
def save(name,array):
    if array.ndim==2:array=np.repeat(array[:,:,None],3,axis=2)
    path=DERIVED/(name+'.png');Image.fromarray(np.uint8(np.clip(array,0,1)*255+.5),'RGB').save(path)
    return path

concrete=np.asarray(Image.open(DECODED/'concrete-mega-slab-a-alt-color.png').convert('RGB'),dtype=np.float64)/255
concrete_r=np.asarray(Image.open(DECODED/'concrete-mega-slab-a-roughness.png').convert('RGB'),dtype=np.float64)[:,:,0]/255
c=np.clip(concrete*.5,0,1);cwet=(.7*c+.3*c*c)*.985
ground_color=save('capture-fg-concrete-primary-wet-basecolor',srgb(cwet**2.2))
ground_rough=save('capture-fg-concrete-primary-wet-roughness',.8125*np.clip(-1+2.5*concrete_r,.005,1)+.01875)
wood=np.asarray(Image.open(DECODED/'scar-wood-rough-a-basecolor.png').convert('RGB'),dtype=np.float64)/255
wood_r=np.asarray(Image.open(DECODED/'scar-wood-rough-a-roughness.png').convert('RGB'),dtype=np.float64)[:,:,0]/255
wood_color=save('capture-fg-scar-wood-primary-basecolor',srgb(np.clip(wood*np.array([.69,.58,.404]),0,1)**2.2))
wood_rough=save('capture-fg-scar-wood-primary-roughness',wood_r*.75)
formulas={'ped-floor-concrete-a':{'basecolor_gamma':'C=saturate(raw*.5); Cwet=lerp(C,C*C,.3)*.985','linear_transfer':'pow(Cwet,2.2)',
    'roughness':'lerp(clamp(-1+2.5*rawR,.005,1),.1,.1875)','uv_scale':1,
    'color':str(ground_color),'normal':str(DECODED/'concrete-mega-slab-a-normal.png'),'roughness_path':str(ground_rough)},
    'ped-wood-base-trim-a-plain':{'basecolor_gamma':'C=saturate(rawSCAR*float3(.69,.58,.404))','linear_transfer':'pow(C,2.2)',
    'roughness':'rawSCAR_R*.75','uv_scale':2,
    'color':str(wood_color),'normal':str(DECODED/'scar-wood-rough-a-normal.png'),'roughness_path':str(wood_rough)}}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
def signature():
    meshes={}
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        coords=np.array([v.co[:] for v in o.data.vertices],dtype='<f4')
        loops=np.array([l.vertex_index for l in o.data.loops],dtype='<u4')
        meshes[o.name]={'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'geometry_sha256':hashlib.sha256(coords.tobytes()+loops.tobytes()).hexdigest()}
    return {'meshes':meshes,'armatures':{o.name:len(o.data.bones) for o in bpy.data.objects if o.type=='ARMATURE'},
        'actions':sorted((a.name,a.users) for a in bpy.data.actions),'frame':bpy.context.scene.frame_current,
        'frame_range':[bpy.context.scene.frame_start,bpy.context.scene.frame_end]}
before=signature()
for key,row in formulas.items():
    mat=bpy.data.materials['M_FG_'+key];mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear()
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    coords=nt.nodes.new('ShaderNodeTexCoord');mapping=nt.nodes.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=(row['uv_scale'],row['uv_scale'],1)
    nt.links.new(coords.outputs['UV'],mapping.inputs['Vector'])
    for channel,path in [('color',row['color']),('normal',row['normal']),('roughness',row['roughness_path'])]:
        img=bpy.data.images.load(path,check_existing=True);img.colorspace_settings.name='sRGB' if channel=='color' else 'Non-Color'
        if not img.packed_file:img.pack()
        img.filepath=bpy.path.relpath(path,start=str(SOURCE.parent))
        node=nt.nodes.new('ShaderNodeTexImage');node.name='FG_CapturePrimary_'+channel;node.image=img
        nt.links.new(mapping.outputs['Vector'],node.inputs['Vector'])
        if channel=='color':nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
        elif channel=='roughness':nt.links.new(node.outputs['Color'],bs.inputs['Roughness'])
        else:
            normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    mat['shader_policy']='Capture-proven primary equations baked for portablePBR; original complex blend attributes/layers not fully ported'
    mat['capture_primary_equations']=json.dumps(row)
assert before==signature(),'FGmaterial edit changed geometry/rig/actions'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
if SOURCE.stem=='Catalog_CapturedFGStage':
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type=='MESH':o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(ROOT/'Exports/Catalog_CapturedFGStage.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'Exports/Catalog_CapturedFGStage.glb'),export_format='GLB',use_selection=True,export_animations=False)
report={'pass':True,'source_blend':str(SOURCE),'source_blend_sha256':digest(SOURCE),'geometry_rig_actions_unchanged':True,'signature':signature(),
    'materials':formulas,'derived_images':[{'path':str(p),'sha256':digest(p)} for p in [ground_color,ground_rough,wood_color,wood_rough]],
    'evidence':'Content/TLOU2/Reports/CAPTURE_FG_SOURCE_PRIMARY_SHADER_PARAMS.json',
    'scope':'Original textures + captured primary tint/roughness/wet defaults and source gamma2.2; no claim of complete layered shader. Portable maps bake at texels, then filter, with8bit sRGB quantization; UE evaluates source equations after sampling.'}
dest=ROOT/'Exports/FGPrimaryMaterialPort';dest.mkdir(exist_ok=True)
(dest/(SOURCE.stem+'.json')).write_text(json.dumps(report,indent=2))
(DERIVED/'derived_texture_manifest.json').write_text(json.dumps({'materials':formulas,'derived_images':report['derived_images'],'scope':report['scope']},indent=2))
print('SOURCE_FG_PRIMARY_MATERIAL_PASS',SOURCE)
