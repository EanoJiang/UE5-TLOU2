"""Restore per-package joint ownership and all twelve original influences.

The human reference contains 520 original SQT records and 554 explicitly
labelled helper fallbacks. Garment and backpack references are separate original
hierarchies. Their authored basis is preserved when joined to one export rig.
"""
import bpy
import copy
import json
from pathlib import Path
import numpy as np
from mathutils import Matrix

ROOT = Path('D:/TLOU2_UE5_8_Codex')
BLEND = ROOT / 'Blender/Ellie_Patrol_Catalog_CaptureMatched.blend'
REST = ROOT / 'Exports/Ellie_CorrectBindRest_SourceMatrices.json'
OUT_REST = ROOT / 'Exports/Ellie_AugmentedBindRest_SourceMatrices.json'
CONFIG = [
    ('hoodie', 'ellie-patrol-hoodie-cloth.pak', 'hoodie__', 'ellie-patrol-hoodie-cloth.json'),
]

def matlist(m):
    return [list(r) for r in m]

def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    arm = bpy.data.objects.get('SK_Ellie_Patrol_Exact')
    assert arm and arm.type == 'ARMATURE'
    human = json.loads(REST.read_text())
    rows = copy.deepcopy(human['rows'])
    human_names = {r['bone_name']: r for r in rows}
    source_human_count = len(rows)
    owned_rigs = []
    pak_rig = {}
    C = Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    for label, pak, prefix, filename in CONFIG:
        source_path = ROOT / 'Exports/OriginalOwnedRigs' / filename
        source = json.loads(source_path.read_text())
        offset = len(rows)
        record = {'id':label, 'source_package':source['source_package'],
                  'source_sha256':source['source_sha256'], 'source_json':str(source_path),
                  'bone_count':source['bone_count'], 'original_sqt_count':source['original_sqt_count'],
                  'combined_bone_offset':offset, 'prefix':prefix, 'rows':[]}
        pak_rig[pak] = record
        for src in source['rows']:
            local_id = src['bone_index']
            combined_parent = offset + src['parent_index'] if src['parent_index'] >= 0 else 0
            global_b = Matrix(src['global_matrix_blender_meters'])
            parent_global_b = (Matrix(source['rows'][src['parent_index']]['global_matrix_blender_meters'])
                               if src['parent_index'] >= 0 else Matrix(rows[0]['global_matrix_blender_meters']))
            local_b = parent_global_b.inverted() @ global_b
            anchor = src.get('ellie_anchor_candidate')
            name = prefix + src['bone_name']
            anchor_name = anchor['bone_name'] if anchor else None
            anchor_offset = None
            if anchor_name:
                anchor_offset = Matrix(human_names[anchor_name]['global_matrix_blender_meters']).inverted() @ global_b
            row = copy.deepcopy(src)
            row.update({'bone_index':offset+local_id, 'bone_name':name,
                        'parent_index':combined_parent, 'rig_owner':label,
                        'owned_source_bone_index':local_id, 'owned_source_bone_name':src['bone_name'],
                        'owned_source_parent_index':src['parent_index'],
                        'local_matrix_game_meters':matlist(C.transposed() @ local_b @ C),
                        'combined_local_matrix_blender_meters':matlist(local_b),
                        'human_anchor_name':anchor_name,
                        'human_anchor_reference_has_sqt':bool(anchor and anchor['source_reference_has_sqt']),
                        'human_anchor_bind_offset_blender':matlist(anchor_offset) if anchor_offset else None,
                        'animation_policy':('human_anchor_delta_preserving_owned_bind_basis' if anchor else
                                            'original_owned_local_reference_no_invented_simulation')})
            rows.append(row)
            record['rows'].append({'combined_bone_index':row['bone_index'], 'bone_name':name,
                                   'owned_source_bone_index':local_id, 'human_anchor_name':anchor_name,
                                   'human_anchor_bind_offset_blender':row['human_anchor_bind_offset_blender'],
                                   'animation_policy':row['animation_policy']})
        owned_rigs.append(record)
    assert len(rows) == 1152
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    arm.animation_data_clear()
    arm.matrix_world = Matrix.Identity(4)
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in list(arm.data.edit_bones):
        if bone.name.startswith('backpack__'):
            arm.data.edit_bones.remove(bone)
    for row in rows[source_human_count:]:
        bone = arm.data.edit_bones.get(row['bone_name']) or arm.data.edit_bones.new(row['bone_name'])
        if bone.name != row['bone_name']:
            raise RuntimeError('bone name truncated: '+row['bone_name'])
        bone.matrix = Matrix(row['global_matrix_blender_meters'])
        bone.length = .025
        bone.use_connect = False
    for row in rows[source_human_count:]:
        arm.data.edit_bones[row['bone_name']].parent = arm.data.edit_bones[rows[row['parent_index']]['bone_name']]
    bpy.ops.object.mode_set(mode='OBJECT')
    for pose in arm.pose.bones:
        pose.matrix_basis = Matrix.Identity(4)
    # Recover raw mesh buffers by their original package and submesh names.
    raw_index = {}
    capture_paths=list((ROOT/'Exports/ExactDebug').glob('*/capture.json'))+list((ROOT/'Exports/BackpackVariantDebug').glob('*/capture.json'))
    for path in capture_paths:
        doc = json.loads(path.read_text())
        pak = Path(doc.get('pak','')).name
        if not pak:
            continue
        for mesh in doc.get('meshes',[]):
            raw_index[(pak,mesh['name'])] = (path.parent,mesh)
    meshes = [o for o in bpy.data.objects if o.type=='MESH' and
              any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)]
    audit = []
    for obj in meshes:
        pak,submesh = obj['source_pak'],obj['source_submesh']
        raw_dir,raw = raw_index[(pak,submesh)]
        z = np.load(raw_dir/raw['npz'])
        if 'bidx_raw' not in z or 'bwgt_raw' not in z:
            raise RuntimeError('Missing original skin buffers: '+obj.name)
        n = len(obj.data.vertices)
        id_dtype='<u2' if raw['bindings']['bidx']['type']==4 else '<u4'
        weight_dtype='<f4' if raw['bindings']['bwgt']['type']==0 else '<u4'
        ids = z['bidx_raw'].view(id_dtype)[:n*12].reshape(n,12)
        values = z['bwgt_raw'].view(weight_dtype)[:n*12].reshape(n,12).astype('float64')
        sums = values.sum(axis=1)
        if not np.all(sums > 0):
            raise RuntimeError('unweighted source vertices: '+obj.name)
        weights = values / sums[:,None]
        rig = pak_rig.get(pak)
        names = [r['bone_name'] for r in rig['rows']] if rig else [r['bone_name'] for r in human['rows']]
        if int(ids[values>0].max()) >= len(names):
            raise RuntimeError('invalid local palette index: '+obj.name)
        for group in list(obj.vertex_groups):
            obj.vertex_groups.remove(group)
        used_ids = sorted(set(int(x) for x in ids[values>0]))
        groups = {i:obj.vertex_groups.new(name=names[i]) for i in used_ids}
        max_influences=0
        for vi in range(n):
            accumulated = {}
            for j in range(12):
                if values[vi,j] > 0:
                    bi=int(ids[vi,j])
                    accumulated[bi]=accumulated.get(bi,0.0)+float(weights[vi,j])
            max_influences=max(max_influences,len(accumulated))
            for bi,weight in accumulated.items():
                groups[bi].add([vi],weight,'REPLACE')
        for mod in obj.modifiers:
            if mod.type=='ARMATURE':
                mod.object=arm
        world=obj.matrix_world.copy()
        obj.parent=arm
        obj.matrix_world=world
        obj['joint_hierarchy_owner']=rig['id'] if rig else 'human'
        obj['source_influence_policy']='all original nonzero of12, normalized per vertex, repeated indices summed'
        actual_error=max(abs(sum(g.weight for g in v.groups)-1.0) for v in obj.data.vertices)
        audit.append({'mesh':obj.name,'source_pak':pak,'owner':obj['joint_hierarchy_owner'],
                      'vertices':n,'used_bones':len(used_ids),'max_influences':max_influences,
                      'max_weight_sum_error':actual_error})
        if actual_error > 2e-7:
            raise RuntimeError('weight normalization error: '+obj.name)
    arm['bind_rest_source']=str(OUT_REST)
    arm['human_original_sqt_bones']=520
    arm['human_helper_identity_fallback']=554
    arm['owned_bones']=78
    doc={'schema':'tlou2_combined_bind_rest_v1','human_reference_source':str(REST),
         'human_bone_count':source_human_count,'human_original_sqt_count':520,
         'human_identity_fallback_count':554,'bone_count':len(rows),'rows':rows,
         'owned_rigs':owned_rigs,
         'owned_animation_policy':'At each frame after applying human pose, set anchored owned global = human animated global @ human anchor bind offset; other owned bones inherit original local reference. No source cloth simulation is invented.',
         'limitations':['Human helper reference beyond original520 is explicitly unresolved.'],
         'selected_backpack':'ellie-backpack.pak uses original mainhuman1074; confirmed capturedGPU vertexcounts8184/3559/1454; prior propbackpack238 superseded'}
    OUT_REST.write_text(json.dumps(doc,indent=2),encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=arm
    fbx=ROOT/'Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx'
    glb=ROOT/'Exports/Ellie_Patrol_Catalog_CaptureMatched.glb'
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True)
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=False,export_all_influences=True)
    bpy.ops.object.select_all(action='DESELECT')
    me=bpy.data.meshes.new('Augmented_SkeletonCarrierMesh')
    me.from_pydata([(0,0,0),(.001,0,0),(0,.001,0)],[],[(0,1,2)])
    ob=bpy.data.objects.new('Augmented_SkeletonCarrier',me)
    bpy.context.collection.objects.link(ob)
    ob.vertex_groups.new(name='root').add([0,1,2],1,'REPLACE')
    ob.modifiers.new('ArmatureDeform','ARMATURE').object=arm
    ob.select_set(True)
    arm.select_set(True)
    carrier=ROOT/'Exports/Ellie_CaptureMatched1152_SkeletonCarrier.fbx'
    bpy.ops.export_scene.fbx(filepath=str(carrier),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,mesh_smooth_type='FACE',use_custom_props=True,use_armature_deform_only=False)
    bpy.data.objects.remove(ob,do_unlink=True)
    report={'blend':str(BLEND),'rest_metadata':str(OUT_REST),'bones':len(arm.data.bones),
            'human_bones':1074,'owned_hoodie_bones':78,'owned_backpack_bones':0,
            'character_meshes':len(meshes),'vertices':sum(r['vertices'] for r in audit),
            'max_source_influences':max(r['max_influences'] for r in audit),
            'mesh_skin_audit':audit,'fbx':str(fbx),'glb':str(glb),'skeleton_carrier':str(carrier)}
    (ROOT/'Exports/owned_rig_integration_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('OWNED_RIG_INTEGRATION',json.dumps({k:v for k,v in report.items() if k!='mesh_skin_audit'}),flush=True)

if __name__=='__main__':
    main()
