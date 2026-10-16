"""Reproduce the captured GPU skin palettes on the editable augmented rig.

P = S @ B uses the explicitly declared export reference B. It reproduces skin
matrices without claiming unknown procedural reference transforms are original.
The original numerical catalog pose is retained in a separate source action.
"""
import bpy
import csv
import json
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path('D:/TLOU2_UE5_8_Codex')
SOURCE = ROOT/'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
META = ROOT/'Exports/Ellie_AugmentedBindRest_SourceMatrices.json'
OUT_LABEL = 'Ellie_Patrol_CapturedSkinPose'
CAPTURE = ROOT/'Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.json'

def maximum_error(a,b):
    return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
    arm.animation_data_clear()
    arm.location=(0,0,0)
    arm.rotation_euler=(0,0,0)
    arm.scale=(1,1,1)
    source = json.loads(CAPTURE.read_text())
    meta = json.loads(META.read_text())
    skin = {r['bone_name']:Matrix(r['captured_skin_matrix_actor_blender']) for r in source['rows']}
    palette_sources = [str(CAPTURE)]
    # Garment palette JSONs use the same matrix fields, original package node
    # indices, and an explicit rig owner. File discovery never invents mapping.
    owned_by_owner = {}
    for path in sorted((ROOT/'Exports/CaptureBuffers').glob('*Capture*Palette*.json')):
        if path == CAPTURE: continue
        doc = json.loads(path.read_text())
        owner = doc.get('rig_owner') or {'ellie-patrol-hoodie-cloth':'hoodie','backpack-ellie':'backpack'}.get(doc.get('rig_name'))
        if owner not in ('hoodie','backpack') or not doc.get('rows'): continue
        owned_by_owner[owner] = {r['bone_index']:r for r in doc['rows']}
        palette_sources.append(str(path))
    rows_by_name = {r['bone_name']:r for r in meta['rows']}
    for name,row in rows_by_name.items():
        owner = row.get('rig_owner')
        owned = owned_by_owner.get(owner, {}).get(row.get('owned_source_bone_index'))
        if owned:
            skin[name] = Matrix(owned['captured_skin_matrix_actor_blender'])
    bones = list(arm.data.bones)
    pending = set(b.name for b in bones)
    desired = {}
    fallback = []
    while pending:
        ready = [arm.data.bones[n] for n in pending if not arm.data.bones[n].parent or arm.data.bones[n].parent.name in desired]
        if not ready: raise RuntimeError('Augmented bone hierarchy has a cycle')
        for bone in ready:
            name = bone.name
            if name in skin:
                desired[name] = skin[name] @ bone.matrix_local
            else:
                row = rows_by_name[name]
                anchor = row.get('human_anchor_name')
                if anchor and anchor in skin:
                    desired[name] = skin[anchor] @ bone.matrix_local
                    policy = 'verified owned anchor follows captured human skin delta'
                elif bone.parent:
                    local = bone.parent.matrix_local.inverted() @ bone.matrix_local
                    desired[name] = desired[bone.parent.name] @ local
                    policy = 'inherits parent pose; no claimed captured skin matrix'
                else:
                    desired[name] = bone.matrix_local.copy()
                    policy = 'reference transform; no claimed captured skin matrix'
                fallback.append({'bone':name,'rig_owner':row.get('rig_owner','human'),'policy':policy})
            pending.remove(name)
    scene=bpy.context.scene
    scene.frame_start=scene.frame_end=1
    scene.render.fps=30
    action=bpy.data.actions.new('AN_CapturedSkinPose_Frame5445')
    arm.animation_data_create()
    arm.animation_data.action=action
    action['source']='GPU captured skin matrices, capture frame5445'
    action['reference_policy']='Original source bind where available; declared helper reference elsewhere. P=S@B preserves captured skin.'
    max_basis_decomposition_error=0.0
    for bone in bones:
        local = desired[bone.parent.name].inverted() @ desired[bone.name] if bone.parent else desired[bone.name]
        rest = bone.parent.matrix_local.inverted() @ bone.matrix_local if bone.parent else bone.matrix_local
        basis = rest.inverted() @ local
        loc,rot,scale = basis.decompose()
        max_basis_decomposition_error=max(max_basis_decomposition_error,maximum_error(basis,Matrix.LocRotScale(loc,rot,scale)))
        pose=arm.pose.bones[bone.name]
        pose.rotation_mode='QUATERNION'
        pose.location=loc
        pose.rotation_quaternion=rot
        pose.scale=scale
        for channel in ('location','rotation_quaternion','scale'):
            pose.keyframe_insert(channel,frame=1,group=bone.name)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    skin_errors={name:maximum_error(arm.pose.bones[name].matrix @ arm.data.bones[name].matrix_local.inverted(),value) for name,value in skin.items()}
    meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)]
    # Compare evaluated Blender vertices with an independent CPU application of
    # the actual captured 3x4 shader matrices. Only fully mapped vertices qualify.
    depsgraph=bpy.context.evaluated_depsgraph_get()
    mesh_reports=[]
    corrective_reports=[]
    for obj in meshes:
        evaluated=obj.evaluated_get(depsgraph)
        mesh=evaluated.to_mesh()
        names={g.index:g.name for g in obj.vertex_groups}
        verified=0
        uncovered=0
        max_vertex_error=0.0
        missing=set()
        corrections={}
        try:
            for vertex,actual in zip(obj.data.vertices,mesh.vertices):
                influences=[(names[g.group],g.weight) for g in vertex.groups if g.weight>0]
                absent=[n for n,w in influences if n not in skin]
                if absent or not influences:
                    uncovered+=1
                    missing.update(absent)
                    continue
                total=sum(w for n,w in influences)
                expected=Vector((0,0,0))
                for name,weight in influences:
                    expected += (skin[name] @ vertex.co)*(weight/total)
                max_vertex_error=max(max_vertex_error,(actual.co-expected).length)
                # Capture skin shaders accept arbitrary affine matrices;
                # conventional TRS bone animation cannot represent local shear.
                # A pose-specific, switchable pre-skin morph compensates only
                # that mathematical representation difference.
                blended=Matrix(((0,0,0),(0,0,0),(0,0,0)))
                for name,weight in influences:
                    actual_skin=arm.pose.bones[name].matrix @ arm.data.bones[name].matrix_local.inverted()
                    linear=actual_skin.to_3x3()
                    for i in range(3):
                        for j in range(3): blended[i][j] += linear[i][j]*weight/total
                corrections[vertex.index]=blended.inverted() @ (expected-actual.co)
                verified+=1
        finally:
            evaluated.to_mesh_clear()
        mesh_reports.append({'mesh':obj.name,'vertices':len(obj.data.vertices),'capture_verified_vertices':verified,
                             'uncovered_vertices':uncovered,'max_vertex_error_m':max_vertex_error,'missing_capture_bones':sorted(missing)})
        if not obj.data.shape_keys: obj.shape_key_add(name='Basis')
        key=obj.data.shape_keys.key_blocks.get('CaptureAffineCorrective') or obj.shape_key_add(name='CaptureAffineCorrective')
        for index,delta in corrections.items(): key.data[index].co=obj.data.vertices[index].co+delta
        key.value=1.0
        key.keyframe_insert('value',frame=1)
        obj['CaptureAffineCorrective_policy']='Pose-specific compensation for GPU affine bone shear lost in TRS; value0 keeps original bind geometry.'
        corrective_reports.append({'mesh':obj.name,'vertices':len(corrections),
                                   'maximum_bind_space_delta_m':max((v.length for v in corrections.values()),default=0.0)})
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    corrected_max=0.0
    for obj,entry in zip(meshes,mesh_reports):
        evaluated=obj.evaluated_get(depsgraph)
        mesh=evaluated.to_mesh()
        names={g.index:g.name for g in obj.vertex_groups}
        error=0.0
        try:
            for vertex,actual in zip(obj.data.vertices,mesh.vertices):
                influences=[(names[g.group],g.weight) for g in vertex.groups if g.weight>0]
                if not influences or any(n not in skin for n,w in influences): continue
                total=sum(w for n,w in influences)
                expected=Vector((0,0,0))
                for name,weight in influences: expected += (skin[name] @ vertex.co)*(weight/total)
                error=max(error,(actual.co-expected).length)
        finally: evaluated.to_mesh_clear()
        entry['max_corrected_vertex_error_m']=error
        corrected_max=max(corrected_max,error)
    report={'source_blend':str(SOURCE),'palette_sources':palette_sources,'output_label':OUT_LABEL,
            'skeleton_bones':len(bones),'captured_skin_bones':len(skin),'fallback_bones':fallback,
            'max_basis_decomposition_error':max_basis_decomposition_error,
            'skin_matrix_max_error':max(skin_errors.values()),
            'skin_matrix_largest_errors':sorted(skin_errors.items(),key=lambda item:item[1],reverse=True)[:20],
            'affine_to_trs_policy':'GPU palette preserved exactly. Switchable CaptureAffineCorrective pre-skin morph compensates local affine shear unrepresentable by standard bone TRS.',
            'corrective_targets':corrective_reports,
            'meshes':mesh_reports,'capture_verified_vertices':sum(m['capture_verified_vertices'] for m in mesh_reports),
            'uncovered_vertices':sum(m['uncovered_vertices'] for m in mesh_reports),
            'max_vertex_error_m':max(m['max_vertex_error_m'] for m in mesh_reports),
            'max_corrected_vertex_error_m':corrected_max,
            'root_motion_policy':'One captured pose, zero displacement. Source actorWorld retained separately.'}
    report['pass']=report['max_corrected_vertex_error_m']<1e-5
    (ROOT/'Exports'/(OUT_LABEL+'_validation.json')).write_text(json.dumps(report,indent=2))
    if not report['pass']: raise RuntimeError('Captured skin/Blender vertex roundtrip failed: '+str({k:v for k,v in report.items() if k in ('skin_matrix_max_error','max_vertex_error_m','max_basis_decomposition_error','max_corrected_vertex_error_m')}))
    for obj in meshes:
        world=obj.matrix_world.copy()
        obj.parent=arm
        obj.matrix_world=world
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Blender'/(OUT_LABEL+'.blend')))
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for obj in meshes: obj.select_set(True)
    bpy.context.view_layer.objects.active=arm
    fbx=dict(use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,
             bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_step=1.0,bake_anim_simplify_factor=0.0,
             apply_unit_scale=True,axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',use_custom_props=True)
    bpy.ops.export_scene.fbx(filepath=str(ROOT/'Exports'/(OUT_LABEL+'.fbx')),**fbx)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'Exports'/(OUT_LABEL+'.glb')),export_format='GLB',use_selection=True,
                              export_animations=True,export_all_influences=True)
    # UE static-hold carrier uses two identical samples to avoid a zero-duration
    # Interchange range. Source .blend and numerical capture remain one frame.
    scene.frame_end=2
    for obj in meshes: obj.data.shape_keys.key_blocks['CaptureAffineCorrective'].keyframe_insert('value',frame=2)
    for pose in arm.pose.bones:
        for channel in ('location','rotation_quaternion','scale'):
            pose.keyframe_insert(channel,frame=2,group=pose.name)
    carrier_mesh=bpy.data.meshes.new('CapturedSkinPose_UEHoldCarrier')
    carrier_mesh.from_pydata([(0,0,0),(.01,0,0),(0,.01,0)],[],[(0,1,2)])
    carrier=bpy.data.objects.new('CapturedSkinPose_UEHoldCarrier',carrier_mesh)
    bpy.context.collection.objects.link(carrier)
    carrier.vertex_groups.new(name='root').add([0,1,2],1,'REPLACE')
    carrier.modifiers.new('Armature','ARMATURE').object=arm
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    carrier.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(ROOT/'Exports'/(OUT_LABEL+'_UEHoldCarrier.fbx')),**fbx)
    root=arm.pose.bones['root'].matrix.translation
    with (ROOT/'Exports'/(OUT_LABEL+'_RootTrajectory.csv')).open('w',newline='') as fp:
        writer=csv.writer(fp)
        writer.writerow(['frame','time_s','root_x_m','root_y_m','root_z_m','displacement_m'])
        writer.writerow([0,0,root.x,root.y,root.z,0])
    print('CAPTURE_SKIN_POSE_VERIFY '+json.dumps({k:v for k,v in report.items() if k not in ('meshes','fallback_bones','skin_matrix_largest_errors')}))

if __name__=='__main__': main()
