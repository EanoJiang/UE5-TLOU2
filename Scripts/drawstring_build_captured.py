"""Apply the verified captured local22 palette and export an exact static hold.

The mesh retains its original neutral basis and normalized original weights.
A switchable pre-skin morph compensates the representation loss from arbitrary
GPU affine palettes to conventional bone TRS and the original packed sum drift.
"""
import bpy
import json
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/Drawstring'
PALETTE=OUT/'Capture_Drawstring_SkinPalette22.json'

def evaluated_positions(obj):
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    try:return np.array([v.co[:] for v in mesh.vertices])
    finally:evaluated.to_mesh_clear()

def main():
    assert PALETTE.exists(),'Capture22 palette is required before posing the export'
    palette=json.loads(PALETTE.read_text())
    rig=json.loads((OUT/'owned_rig22.json').read_text())
    rows={r['bone_index']:r for r in palette['rows']}
    assert set(rows)==set(range(22)),('incomplete original local22 palette',sorted(rows))
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_Drawstrings.blend'))
    arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    obj=next(o for o in bpy.data.objects if o.type=='MESH')
    names=[r['bone_name'] for r in rig['rows']]
    skin={names[i]:Matrix(rows[i]['captured_skin_matrix_actor_blender']) for i in range(22)}
    arm.animation_data_clear()
    desired={name:skin[name]@arm.data.bones[name].matrix_local for name in names}
    action=bpy.data.actions.new('AN_Ellie_Patrol_Drawstrings_CapturedHold')
    action['source_palette']=str(PALETTE)
    action['pose_policy']='one original GPU captured pose, two identical hold samples, no invented simulation'
    arm.animation_data_create()
    arm.animation_data.action=action
    max_basis_decomposition_error=0.
    for name in names:
        bone=arm.data.bones[name]
        local=desired[bone.parent.name].inverted()@desired[name] if bone.parent else desired[name]
        rest=bone.parent.matrix_local.inverted()@bone.matrix_local if bone.parent else bone.matrix_local
        basis=rest.inverted()@local
        loc,rot,scale=basis.decompose()
        reconstructed=Matrix.LocRotScale(loc,rot,scale)
        max_basis_decomposition_error=max(max_basis_decomposition_error,max(abs(basis[i][j]-reconstructed[i][j]) for i in range(4) for j in range(4)))
        pose=arm.pose.bones[name]
        pose.rotation_mode='QUATERNION'
        pose.location=loc
        pose.rotation_quaternion=rot
        pose.scale=scale
        for frame in (1,2):
            for channel in ('location','rotation_quaternion','scale'):
                pose.keyframe_insert(channel,frame=frame,group=name)
    scene=bpy.context.scene
    scene.frame_start=1
    scene.frame_end=2
    scene.render.fps=30
    scene.frame_set(1)
    bpy.context.view_layer.update()
    doc=json.loads((OUT/'capture.json').read_text())
    source=next(x for x in doc['meshes'] if '_LODShape0_' in x['name'])
    z=np.load(OUT/source['npz'])
    ids=z['bidx_raw'].view('<u2').reshape(441,12)
    values=z['bwgt_raw'].view('<u4').reshape(441,12)
    positions=np.array([v.co[:] for v in obj.data.vertices])
    homogeneous=np.column_stack((positions,np.ones(441)))
    matrices=np.array([skin[name] for name in names])
    factor=np.array([0x34800002],dtype='<u4').view('<f4')[0]
    shader_weights=values.astype(np.float32)*factor
    target=np.einsum('nijk,nk,ni->nj',matrices[ids][:,:,:3,:],homogeneous,shader_weights.astype(float),optimize=True)
    pre=evaluated_positions(obj)
    max_pre_error=float(np.linalg.norm(pre-target,axis=1).max())
    actual_skin={name:arm.pose.bones[name].matrix@arm.data.bones[name].matrix_local.inverted() for name in names}
    group_names={g.index:g.name for g in obj.vertex_groups}
    obj.shape_key_add(name='Basis')
    corrective=obj.shape_key_add(name='CaptureAffineCorrective')
    delta_max=0.
    for vi,vertex in enumerate(obj.data.vertices):
        blended=np.zeros((3,3))
        total=sum(g.weight for g in vertex.groups)
        for group in vertex.groups:
            blended+=np.array(actual_skin[group_names[group.group]].to_3x3())*(group.weight/total)
        delta=np.linalg.solve(blended,target[vi]-pre[vi])
        corrective.data[vi].co=vertex.co+Vector(delta)
        delta_max=max(delta_max,float(np.linalg.norm(delta)))
    corrective.value=1.
    for frame in (1,2):corrective.keyframe_insert('value',frame=frame)
    obj['CaptureAffineCorrective_policy']='Pose-specific GPU affine/TRS and packed weight-sum compensation; original neutral geometry retained in Basis'
    bpy.context.view_layer.update()
    actual=evaluated_positions(obj)
    error=float(np.linalg.norm(actual-target,axis=1).max())
    assert error<1e-5,('captured shader/Blender error',error)
    ue=target*np.array([100.,-100.,100.])
    np.savez_compressed(OUT/'captured_reference.npz',
        captured_positions_actor_blender_m=target,captured_positions_actor_ue_cm=ue,
        original_positions_actor_blender_m=positions,source_bone_indices=ids,
        source_weight_values_typed=values,source_shader_weights_float32=shader_weights)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=arm
    bpy.ops.file.pack_all()
    captured_blend=ROOT/'Blender/Ellie_Patrol_Drawstrings_Captured.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(captured_blend))
    fbx_settings=dict(use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,
        bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,bake_anim_step=1.,bake_anim_simplify_factor=0.,
        apply_unit_scale=True,axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',
        secondary_bone_axis='X',use_armature_deform_only=False,use_custom_props=True,mesh_smooth_type='FACE')
    bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_Ellie_Patrol_Drawstrings.fbx'),**fbx_settings)
    report=dict(pass_=True,palette=str(PALETTE),blend=str(captured_blend),
        fbx=str(OUT/'SK_Ellie_Patrol_Drawstrings.fbx'),
        animation_action=action.name,morph_name=corrective.name,morph_value=1.,
        frames=[1,2],fps=30,root_displacement_m=0.,vertices=441,triangles=736,bones=22,
        maximum_trs_basis_decomposition_component_error=max_basis_decomposition_error,
        max_uncorrected_shader_vertex_error_m=max_pre_error,
        max_corrected_shader_vertex_error_m=error,maximum_bind_space_corrective_delta_m=delta_max,
        reference_npz=str(OUT/'captured_reference.npz'),
        ue_reference_key='captured_positions_actor_ue_cm',
        shader_weight_policy='float32(uint22)*asfloat(0x34800002), no shader normalization',
        normal_policy='computed from original triangles; packed normal stream130 retained in source PAK; no full source pixel equivalence claimed',
        capture_temporal_scope=palette.get('temporal_scope','See source palette metadata'),
        capture_pose_limitation='Coherent captured resident22 palette with verified named anchors; not proven exact final draw-event state. Eight plausible matching-anchor palettes vary in8 simulation bones; one additional matching-anchor candidate has corrupt simulated records and is excluded.')
    report['pass']=report.pop('pass_')
    (OUT/'captured_build.json').write_text(json.dumps(report,indent=2))
    print('DRAWSTRING_CAPTURED_BUILD '+json.dumps(report))

if __name__=='__main__':main()
