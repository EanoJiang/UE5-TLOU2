"""Refresh the extracted patrol source with high-res PC textures and cutout masks."""
import bpy, os, json, math
import numpy as np
from mathutils import Vector

ROOT="D:/TLOU2_UE5_8_Codex"
BLEND=ROOT+"/Blender/Ellie_Patrol_Catalog_Exact.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)
for image in bpy.data.images:
    if image.source=='FILE':
        try: image.reload()
        except Exception: pass

# The extraction has no unpacked vertex normal binding. Flat shading is a
# Blender creation default, not the game asset's intended shading.
for ob in bpy.data.objects:
    if ob.type=='MESH':
        for poly in ob.data.polygons: poly.use_smooth=True

MASK={
 'hair-base':'ellie-hair-thick-trans',
 'hair-thick':'ellie-hair-thick-trans','hair-thick-alpha':'ellie-hair-thick-trans',
 'hair-thin':'ellie-hair-thin-trans','hair-thin-alpha':'ellie-hair-thin-trans',
 'hair-thin-wet':'ellie-hair-thin-wet-trans','hair-flying-alpha':'ellie-hair-flying-trans',
 'eyebrows':'ellie-brows-trans','eyelashes':'ellie-eyelashes-trans',
}
report=[]
for mat in bpy.data.materials:
    if not mat.name.startswith('M_ND_') or not mat.use_nodes:continue
    nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');key=mat.name[5:]
    if not bs:continue
    row={'material':mat.name}
    # Reconstruct Z for packed BC7 normal RG: the B plane is an auxiliary
    # channel in the ND skin/wrinkle texture, not tangent-space Z.
    normal_node=nt.nodes.get('ND_Normal_'+key)
    if normal_node and normal_node.image:
        img=normal_node.image
        img.colorspace_settings.name='Non-Color'
        nm=nt.nodes.get('ND_NormalMap_'+key)
        if nm:
            nm.inputs['Strength'].default_value=0.6
            if key=='head':
                # R/G from the packed source; shader derives positive Z.
                sep=nt.nodes.get('ND_UnpackRG') or nt.nodes.new('ShaderNodeSeparateColor');sep.name='ND_UnpackRG';nt.links.new(normal_node.outputs['Color'],sep.inputs[0])
                comb=nt.nodes.get('ND_NormalXYZ') or nt.nodes.new('ShaderNodeCombineXYZ');comb.name='ND_NormalXYZ'
                nt.links.new(sep.outputs['Red'],comb.inputs['X']);nt.links.new(sep.outputs['Green'],comb.inputs['Y'])
                # Z~1 is a stable approximation for this low-amplitude map.
                comb.inputs['Z'].default_value=1.0
                nt.links.new(comb.outputs[0],nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
            row['normal']=img.filepath
    path=ROOT+'/Exports/TexturesDecoded/'+MASK.get(key,'')+'.png'
    if key in MASK and os.path.isfile(path):
        img=bpy.data.images.load(path,check_existing=True);img.colorspace_settings.name='Non-Color'
        node=nt.nodes.get('ND_Opacity_'+key) or nt.nodes.new('ShaderNodeTexImage');node.name='ND_Opacity_'+key;node.image=img
        nt.links.new(node.outputs['Color'],bs.inputs['Alpha'])
        mat.surface_render_method='DITHERED'
        mat.use_transparency_overlap=False
        mat['decoded_opacity_texture']=path
        row['opacity']=path
    # Skin and garment roughness remain deliberately simple PBR parameters.
    bs.inputs['Roughness'].default_value=.64 if key in ('head','arms') else .8
    report.append(row)

sc=bpy.context.scene;sc.frame_set(1);sc.render.engine='BLENDER_EEVEE_NEXT'
sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.render.filepath=ROOT+'/Exports/TextureDiagnostic/HighRes_Shaded_Full.png'
bpy.ops.render.render(write_still=True)
cam=sc.camera;oldloc=cam.location.copy();oldrot=cam.rotation_euler.copy();oldlens=cam.data.lens
cam.location=(.65,-1.65,1.78);cam.data.lens=62;cam.rotation_euler=(Vector((0,0,1.47))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.filepath=ROOT+'/Exports/TextureDiagnostic/HighRes_Shaded_Head.png'
bpy.ops.render.render(write_still=True)
cam.location=oldloc;cam.rotation_euler=oldrot;cam.data.lens=oldlens
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
json.dump(report,open(ROOT+'/Exports/TextureDiagnostic/material_repair.json','w'),indent=2)
print('BLENDER_PATROL_MATERIAL_REPAIR',len(report))
