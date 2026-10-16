"""Export a capture-resident Ellie skin palette with independent pose matching.

The actual float3x4 records multiply source bind-space vertices. They are skin
matrices (posed_global @ inverse_bind), rather than local S/Q/T bone records.
"""
import hashlib,json,math
from pathlib import Path
import numpy as np
from ngfx_resource_reader import read_resource,resource_pages
from export_owned_clothing_skeletons import sqt_matrix

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/CaptureBuffers'
C=np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]],float)
UID=7556
OFFSET=125371136
COUNT=1038


def main():
    rest=json.loads((ROOT/'Exports/Ellie_CorrectBindRest_SourceMatrices.json').read_text())['rows']
    pose=json.loads((ROOT/'Exports/AnimationSources/DecodedOriginal/model-viewer-ellie-16-patrol.json').read_text())
    tracks={r['bone_index']:r for r in pose['tracks']}
    predicted_global=[];predicted_skin=[]
    for row in rest:
        index=row['bone_index'];parent=row['parent_index'];t=tracks.get(index)
        local=sqt_matrix(t['scale'],t['rotations_xyzw'][0],t['translation']) if t else np.array(row['local_matrix_game_meters'])
        global_matrix=predicted_global[parent]@local if parent>=0 else local
        predicted_global.append(global_matrix)
        predicted_skin.append(global_matrix@np.linalg.inv(row['global_matrix_game_meters']))
    raw=read_resource(UID,OFFSET,COUNT*48)
    matrices=np.repeat(np.eye(4)[None,:,:],COUNT,axis=0)
    matrices[:,:3,:]=np.frombuffer(raw,'<f4').reshape(COUNT,3,4)
    actor_world=matrices[0]@np.linalg.inv(predicted_skin[0])
    actor_inverse=np.linalg.inv(actor_world)
    actor_matrices=actor_inverse@matrices
    expected=actor_world@np.array(predicted_skin[:COUNT])
    errors=np.max(abs(matrices-expected),axis=(1,2))
    verified_indices=[i for i in list(range(143))+list(range(322,360)) if i not in [8,9]]
    max_primary=float(max(errors[i]for i in verified_indices))
    if max_primary>2e-6:raise ValueError(('source/capture skin match failed',max_primary))
    rows=[];pose_globals=[]
    for index in range(COUNT):
        ref=rest[index];bind=np.array(ref['global_matrix_game_meters'])
        # This is an exact presentation pose relative to the CHOSEN export
        # reference. It does not claim to infer the original unknown helper B.
        chosen_global=actor_matrices[index]@bind;pose_globals.append(chosen_global)
        parent=ref['parent_index']
        chosen_local=np.linalg.inv(pose_globals[parent])@chosen_global if parent>=0 else chosen_global
        rows.append(dict(bone_index=index,bone_name=ref['bone_name'],parent_index=parent,
            captured_skin_matrix_game=matrices[index].tolist(),
            captured_skin_matrix_actor_game=actor_matrices[index].tolist(),
            captured_skin_matrix_blender=(C@matrices[index]@C.T).tolist(),
            captured_skin_matrix_actor_blender=(C@actor_matrices[index]@C.T).tolist(),
            chosen_reference_global_game=bind.tolist(),
            capture_presentation_global_game=chosen_global.tolist(),
            capture_presentation_local_game=chosen_local.tolist(),
            capture_presentation_global_blender=(C@chosen_global@C.T).tolist(),
            reference_is_original_sqt=ref['original_local_sqt_available'],
            original_bind_reference_policy=ref['reference_policy'],
            error_vs_source_viewer_skin=float(errors[index])))
    reconstructed=np.array(pose_globals)@np.linalg.inv(np.array([r['global_matrix_game_meters']for r in rest[:COUNT]]))
    roundtrip=float(np.max(abs(reconstructed-actor_matrices)))
    if roundtrip>1e-12:raise ValueError('chosen reference skin roundtrip')
    rotation_angle=math.degrees(math.atan2(actor_world[0,2],actor_world[0,0]))
    doc=dict(schema='tlou2.capture-skin-palette.v1',capture_file='D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture',
        capture_frame=5445,source=dict(resource_uid=UID,resource_offset=OFFSET,bytes=len(raw),
        chunk_id=2708,chunk_byte_offset=1639168,sha256=hashlib.sha256(raw).hexdigest(),
        mapping_method='initial object UID7556 state references contiguous2MiB data pages; this palette is resident in chunk2708; direct original bone index order verified against179sourcebody/finger transforms'),
        matrix_semantics='column-vector affine skin matrices: capturedSkin = actorWorld @ posedGlobal @ inverse(bindGlobal). Source bind-space vertices multiply this matrix.',
        matrix_layout='three consecutive float4 rows (48bytes); implicit bottom row[0,0,0,1]',
        valid_matrix_count=COUNT,source_hierarchy_node_count=1074,
        unresolved_node_indices=list(range(COUNT,1074)),
        unresolved_node_policy='sourcegroup7 bow-string/external helpers have no originalSQT and are unused byselectedcharacter meshes; allocatedtailbytes are not claimed asvalidatedskinmatrices',
        actor_world_game=actor_world.tolist(),actor_world_blender=(C@actor_world@C.T).tolist(),actor_y_rotation_degrees=rotation_angle,
        source_pose='model-viewer-ellie-16-patrol',source_pose_package=pose['source'],
        verification=dict(pass_=True,verified_original_body_finger_bones=len(verified_indices),
            body_bones_verified=141,finger_bones_verified=38,maximum_source_match_error=max_primary,
            eyes_excluded_as_live_procedural=[8,9],all_valid_matrix_components_finite=bool(np.isfinite(matrices).all()),
            chosen_reference_skin_matrix_roundtrip_max_error=roundtrip,
            facial_and_helper_differences='capture skin matrices include live facial/procedural state beyond the original gallery constant pose'),
        chosen_reference_policy='The520 originalsourceSQT bindrecords remain untouched. Unknownhelperbinds retain their explicitlydeclared exportreference. Capturepresentation globals are derived from capturedSkin @ chosenB so skinning reproduces theframe exactly; they are not originalhelperbindrest claims.',rows=rows)
    doc['verification']['pass']=doc['verification'].pop('pass_')
    target=OUT/'Ellie_Capture_SkinPalette1038.json';target.write_text(json.dumps(doc,indent=2))
    (OUT/'Ellie_Capture_SkinPalette1038.bin').write_bytes(raw)
    np.savez(OUT/'Ellie_Capture_SkinPalette1038.npz',captured_skin_game=matrices,captured_skin_actor_game=actor_matrices,actor_world_game=actor_world,
        chosen_reference_capture_globals_game=np.array(pose_globals),source_comparison_error=errors)
    print(json.dumps(dict(path=str(target),source=doc['source'],verification=doc['verification'],actor_world_game=doc['actor_world_game']),indent=2))


if __name__=='__main__':main()
