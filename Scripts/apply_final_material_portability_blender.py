"""Pack used images and align the portable DCC eye-corner materials with UE.

This changes only materials and image storage; geometry, armature and actions
are checked before/after and never edited.
"""
import bpy,json,sys,os
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
SOURCE=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

def signature():
    return {'meshes':{o.name:len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'},
            'armatures':{o.name:len(o.data.bones) for o in bpy.data.objects if o.type=='ARMATURE'},
            'actions':sorted((a.name,a.users) for a in bpy.data.actions),
            'object_actions':{o.name:o.animation_data.action.name for o in bpy.data.objects if o.animation_data and o.animation_data.action},
            'frame':bpy.context.scene.frame_current,'frame_start':bpy.context.scene.frame_start,'frame_end':bpy.context.scene.frame_end}

before=signature()
def image(stem,space):
    im=bpy.data.images.load(str(ROOT/'Exports/TexturesDecoded'/(stem+'.png')),check_existing=True)
    im.colorspace_settings.name=space
    return im
def texture(mat,name,stem,channel):
    nt=mat.node_tree
    bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    node=nt.nodes.get(name) or nt.nodes.new('ShaderNodeTexImage')
    node.name=name
    node.image=image(stem,'Non-Color' if channel=='Normal' else 'sRGB')
    if channel=='Normal':
        nm=nt.nodes.get(name+'_Map') or nt.nodes.new('ShaderNodeNormalMap')
        nm.name=name+'_Map'
        nt.links.new(node.outputs['Color'],nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    else:nt.links.new(node.outputs['Color'],bs.inputs[channel])
    mat['decoded_'+('normal' if channel=='Normal' else 'color')+'_texture']=str(ROOT/'Exports/TexturesDecoded'/(stem+'.png'))
tearduct=bpy.data.materials.get('M_ND_tearduct')
if tearduct:
    texture(tearduct,'Final_Tearduct_Color','ellie-caruncle-color','Base Color')
    texture(tearduct,'Final_Tearduct_Normal','ellie-caruncle-normal','Normal')
    tearduct.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
    tearduct['material_policy']='original decoded caruncle color/normal; generic PBR roughness matches UE'
tears=bpy.data.materials.get('M_ND_tears')
if tears:
    texture(tears,'Final_Tear_Normal','tear-normal','Normal')
    bs=tears.node_tree.nodes.get('Principled BSDF')
    for link in list(bs.inputs['Alpha'].links):tears.node_tree.links.remove(link)
    bs.inputs['Alpha'].default_value=.08
    bs.inputs['Roughness'].default_value=.12
    bs.inputs['Base Color'].default_value=(.18,.18,.18,1)
    tears.surface_render_method='DITHERED'
    tears.use_transparency_overlap=False
    tears['material_policy']='portable translucent tear film alpha.08/roughness.12; no original refraction/flow claimed; normal matches current UE selected source'

def reachable_images(node,visited):
    if node in visited:return set()
    visited.add(node)
    out={node.image} if node.type=='TEX_IMAGE' and node.image else set()
    for inp in node.inputs:
        for link in inp.links:out.update(reachable_images(link.from_node,visited))
    return out
used=set()
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    for mat in ob.data.materials:
        if not mat or not mat.use_nodes:continue
        for node in mat.node_tree.nodes:
            if node.type=='OUTPUT_MATERIAL' and node.is_active_output:
                used.update(reachable_images(node,set()))
packed=[]
for im in sorted(used,key=lambda x:x.name):
    original=bpy.path.abspath(im.filepath)
    if not im.packed_file:
        if not os.path.isfile(original):raise RuntimeError('missing active image '+original)
        im.pack()
    if original and os.path.isfile(original):im.filepath=bpy.path.relpath(original,start=str(SOURCE.parent))
    packed.append({'image':im.name,'source_filepath':original,'portable_filepath':im.filepath,'packed':bool(im.packed_file),'dimensions':list(im.size)})
# Referenced inactive source maps remain portable with the project texture tree.
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:
        original=bpy.path.abspath(im.filepath)
        if os.path.isfile(original) and os.path.normcase(original).startswith(os.path.normcase(str(ROOT))):
            im.filepath=bpy.path.relpath(original,start=str(SOURCE.parent))
after=signature()
assert before==after,('geometry/action state changed',before,after)
assert all(r['packed'] for r in packed)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
out={'blend':str(SOURCE),'used_image_count':len(packed),'packed_image_count':len(packed),
     'geometry_actions_unchanged':before==after,'identity_signature':after,'images':packed,
     'DCC_material_changes':['tearduct uses originalcaruncle color+normal','tearfilm uses originaltear-normal and documentedUEportable alpha.08 roughness.12']}
dest=ROOT/'Exports/MaterialPortability'
dest.mkdir(exist_ok=True)
(dest/(SOURCE.stem+'.json')).write_text(json.dumps(out,indent=2),encoding='utf-8')
print('FINAL_MATERIAL_PORTABILITY',SOURCE,len(packed),before==after)
