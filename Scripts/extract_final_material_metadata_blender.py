import bpy,json,os
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
SOURCE=ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
arm=bpy.data.objects['SK_Ellie_Patrol_Exact']
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)]
def image_info(image):
    path=bpy.path.abspath(image.filepath)
    return {'image':image.name,'filepath':image.filepath,'absolute_filepath':path,
            'file_exists':os.path.isfile(path),'packed':bool(image.packed_file),
            'dimensions':list(image.size),'colorspace':image.colorspace_settings.name}
def dependencies(socket,visited=None):
    if visited is None:visited=set()
    out=[]
    for link in socket.links:
        node=link.from_node
        if node.name in visited:continue
        visited.add(node.name)
        if node.type=='TEX_IMAGE' and node.image:
            out.append({'node':node.name,'output':link.from_socket.name,**image_info(node.image)})
        for inp in node.inputs:
            if inp.is_linked:out.extend(dependencies(inp,visited))
    return out
materials={}
rows=[]
for mesh in meshes:
    slots=[]
    for material in mesh.data.materials:
        if not material:continue
        slots.append(material.name)
        if material.name in materials:continue
        nt=material.node_tree
        principled=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
        channels={}
        if principled:
            for name in ['Base Color','Normal','Roughness','Metallic','Alpha','Specular IOR Level','Subsurface Weight']:
                inp=principled.inputs.get(name)
                if inp is None:continue
                val=inp.default_value
                channels[name]={'linked':inp.is_linked,'default':float(val) if isinstance(val,(int,float)) else list(val),'images':dependencies(inp)}
        materials[material.name]={'name':material.name,'source_material_key':material.name[5:] if material.name.startswith('M_ND_') else None,
                                  'channels':channels,'properties':dict(material.items()),
                                  'surface_render_method':material.surface_render_method,
                                  'use_transparency_overlap':material.use_transparency_overlap,
                                  'all_image_nodes':[{'node':n.name,**image_info(n.image)} for n in nt.nodes if n.type=='TEX_IMAGE' and n.image]}
    rows.append({'object':mesh.name,'source_pak':mesh.get('source_pak'),'source_submesh':mesh.get('source_submesh'),
                 'source_material':mesh.get('source_material'),'joint_owner':mesh.get('joint_hierarchy_owner'),
                 'vertices':len(mesh.data.vertices),'materials':slots})
active_images={im['absolute_filepath']:im for material in materials.values() for channel in material['channels'].values() for im in channel['images']}
out={'blend':str(SOURCE),'armature':arm.name,'bones':len(arm.data.bones),'meshes':rows,
     'materials':materials,'active_character_images':list(active_images.values()),
     'portability':{'active_image_count':len(active_images),'packed_active_image_count':sum(i['packed'] for i in active_images.values()),
                    'missing_active_images':[i['absolute_filepath'] for i in active_images.values() if not i['file_exists'] and not i['packed']],
                    'absolute_external_active_images':[i['filepath'] for i in active_images.values() if not i['packed'] and not i['filepath'].startswith('//') and os.path.isabs(i['filepath'])]}}
path=ROOT/'Exports/final_blender_material_metadata.json'
path.write_text(json.dumps(out,indent=2),encoding='utf-8')
print('FINAL_MATERIAL_METADATA',len(rows),len(materials),out['portability'])
