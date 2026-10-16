import bpy,sys
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
SOURCE=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
mat=bpy.data.materials['M_ND_eyes']
nt=mat.node_tree
bs=nt.nodes.get('Principled BSDF')
for name,channel,file,space in [('Reconstructed_Eye_BaseColor','Base Color','ellie-eyes-reconstructed-basecolor.png','sRGB'),('Reconstructed_Eye_Normal','Normal','ellie-eyes-reconstructed-normal.png','Non-Color')]:
    node=nt.nodes.get(name) or nt.nodes.new('ShaderNodeTexImage')
    node.name=name
    node.image=bpy.data.images.load(str(ROOT/'Exports/TexturesDecoded'/file),check_existing=True)
    node.image.colorspace_settings.name=space
    if channel=='Normal':
        normal=nt.nodes.get('Reconstructed_Eye_NormalMap') or nt.nodes.new('ShaderNodeNormalMap')
        normal.name='Reconstructed_Eye_NormalMap'
        nt.links.new(node.outputs['Color'],normal.inputs['Color'])
        nt.links.new(normal.outputs['Normal'],bs.inputs[channel])
    else:nt.links.new(node.outputs['Color'],bs.inputs[channel])
bs.inputs['Roughness'].default_value=.18
bs.inputs['Specular IOR Level'].default_value=.5
mat['shader_reconstruction']='portable radialiris sclera blend; scale3.2 inferred, originalconstant unresolved'
mat['decoded_color_texture']=str(ROOT/'Exports/TexturesDecoded/ellie-eyes-reconstructed-basecolor.png')
mat['decoded_normal_texture']=str(ROOT/'Exports/TexturesDecoded/ellie-eyes-reconstructed-normal.png')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
print('EYE_MATERIAL_RECONSTRUCTION_APPLIED',str(SOURCE))
