"""Build the omitted LOD0 mesh and its independent authored 22-bone rig."""
import bpy
import json
import shutil
from pathlib import Path
import numpy as np
from mathutils import Matrix

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/Drawstring'
C=np.array([[1,0,0],[0,0,-1],[0,1,0]],float)

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=1.
    doc=json.loads((OUT/'capture.json').read_text())
    rig=json.loads((OUT/'owned_rig22.json').read_text())
    source=next(x for x in doc['meshes'] if '_LODShape0_' in x['name'])
    raw=np.load(OUT/source['npz'])
    n=source['vertex_count']
    positions=raw['pos_raw'].view('<f4')[:n*3].reshape(n,3)
    indices=raw['indices_raw'].view('<u2')[:source['count']].reshape(-1,3)
    arm_data=bpy.data.armatures.new('SKEL_Ellie_Patrol_Drawstrings22')
    arm=bpy.data.objects.new('DrawstringArmature',arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active=arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for row in rig['rows']:
        bone=arm_data.edit_bones.new(row['bone_name'])
        assert bone.name==row['bone_name']
        bone.matrix=Matrix(row['global_matrix_blender_meters'])
        bone.length=.015
    for row in rig['rows']:
        if row['parent_index']>=0:
            arm_data.edit_bones[row['bone_name']].parent=arm_data.edit_bones[rig['rows'][row['parent_index']]['bone_name']]
    bpy.ops.object.mode_set(mode='OBJECT')
    arm['source_pak']=doc['pak']
    arm['source_local_rig_bones']=22
    mesh_data=bpy.data.meshes.new('Ellie_Patrol_Drawstrings_LOD0')
    mesh_data.from_pydata((positions@C.T).tolist(),[],indices.tolist())
    mesh_data.update()
    obj=bpy.data.objects.new('SK_Ellie_Patrol_Drawstrings',mesh_data)
    bpy.context.collection.objects.link(obj)
    for key in ('uv0','uv1'):
        uv=raw[key+'_raw'].view('<f4').reshape(n,2)
        layer=mesh_data.uv_layers.new(name='UVMap' if key=='uv0' else 'UV2')
        for li,loop in enumerate(mesh_data.loops):
            u,v=uv[loop.vertex_index]
            layer.data[li].uv=(float(u),1.-float(v))
    ids=raw['bidx_raw'].view('<u2').reshape(n,12)
    values=raw['bwgt_raw'].view('<u4').reshape(n,12).astype(float)
    weights=values/values.sum(1)[:,None]
    names=[r['bone_name'] for r in rig['rows']]
    groups={i:obj.vertex_groups.new(name=names[i]) for i in np.unique(ids[values>0])}
    for vi in range(n):
        accumulated={}
        for bi,w,raw_w in zip(ids[vi],weights[vi],values[vi]):
            if raw_w>0:accumulated[int(bi)]=accumulated.get(int(bi),0.)+float(w)
        for bi,w in accumulated.items():groups[bi].add([vi],w,'REPLACE')
    obj.parent=arm
    obj.modifiers.new('DrawstringSkin','ARMATURE').object=arm
    obj['source_pak']=doc['pak']
    obj['source_submesh']=source['name']
    obj['source_material']=source['material']
    obj['source_raw_buffers']=str(OUT/source['npz'])
    obj['weight_policy']='all positive original packed weights normalized for DCC; original typed records preserved in NPZ'
    material=bpy.data.materials.new('M_Drawstring_SourceHoodie')
    material.use_nodes=True
    bs=material.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(.23,.23,.22,1)
    bs.inputs['Roughness'].default_value=.8
    material['source_material']=source['material']
    mesh_data.materials.append(material)
    # Shared source hoodie maps give the isolated editable asset its original atlas.
    for label,filename,colorspace in [('Color','ellie-patrol-hoodie-up-color.png','sRGB'),('Normal','ellie-patrol-hoodie-up-normal.png','Non-Color')]:
        path=ROOT/'Exports/TexturesDecoded'/filename
        if not path.exists():continue
        tex=material.node_tree.nodes.new('ShaderNodeTexImage')
        tex.label=label
        tex.image=bpy.data.images.load(str(path),check_existing=True)
        tex.image.colorspace_settings.name=colorspace
        if label=='Color':material.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        else:
            normal=material.node_tree.nodes.new('ShaderNodeNormalMap')
            material.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color'])
            material.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    for p in mesh_data.polygons:p.use_smooth=True
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=arm
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_Drawstrings.blend'))
    bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_Ellie_Patrol_Drawstrings.fbx'),
        use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,
        bake_anim=False,use_armature_deform_only=False,use_custom_props=True,
        apply_unit_scale=True,axis_forward='-Z',axis_up='Y',
        primary_bone_axis='Y',secondary_bone_axis='X',mesh_smooth_type='FACE')
    shutil.copyfile(OUT/'SK_Ellie_Patrol_Drawstrings.fbx',OUT/'SK_Ellie_Patrol_Drawstrings_Neutral.fbx')
    report=dict(blend=str(ROOT/'Blender/Ellie_Patrol_Drawstrings.blend'),
        fbx=str(OUT/'SK_Ellie_Patrol_Drawstrings.fbx'),mesh_name=obj.name,
        armature_name=arm.name,vertices=n,triangles=len(indices),bones=len(rig['rows']),
        source_uv_channels=2,max_source_positive_influences=int((values>0).sum(1).max()),
        source_position_basis='game Y-up meters -> Blender (x,-z,y) meters',
        fbx_unit_policy='meter source, apply_unit_scale=True, standard FBX centimeter conversion',
        source_normal_policy='source packed stream130 retained in PAK; neutral Blender normals computed from original triangles',
        capture_pose_status='pending separate captured22 palette')
    (OUT/'blender_build.json').write_text(json.dumps(report,indent=2))
    print('DRAWSTRING_BLENDER_BUILD '+json.dumps(report))

if __name__=='__main__':main()
