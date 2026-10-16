"""Locate imported reference, raw track, compression or retarget divergence."""
from pathlib import Path
import json
import numpy as np
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/BoneDeformationDiagnostic'
source=json.loads((OUT/'blender_capture_bones1152.json').read_text())
src={r['bone']:r for r in source['rows']}
ue=json.loads((OUT/'ue_capture_bone_poses.json').read_text())
def matrix(t):
    m=np.eye(4)
    q=np.asarray(t['rotation_xyzw'],dtype=float)
    x,y,z,w=q/np.linalg.norm(q)
    rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
        [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
        [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m[:3,:3]=rotation@np.diag(t['scale'])
    m[:3,3]=t['translation']
    return m
def compare(a,b):
    return {'max_matrix_error':float(np.abs(a-b).max()),
        'linear_matrix_error':float(np.abs(a[:3,:3]-b[:3,:3]).max()),
        'translation_error_cm':float(np.linalg.norm(a[:3,3]-b[:3,3]))}
def summary(rows,field):
    return sorted([(r['bone'],r[field])for r in rows],key=lambda r:r[1],reverse=True)[:25]
rows=[]
for name,r in src.items():
    ref=ue['skeleton_reference'][name]
    reference=matrix(ref['global'])
    expectedref=np.array(r['rest_global_ue_cm'])
    expectedpose=np.array(r['pose_global_ue_cm'])
    # FBX importer retains the Blender meter->centimeter factor on the
    # synthetic armature root, leaving every child local translation in meters.
    expectedref[:3,:3]*=100.
    expectedpose[:3,:3]*=100.
    expectedreflocal=np.array(r['rest_local_ue_cm'])
    expectedposelocal=np.array(r['pose_local_ue_cm'])
    expectedreflocal[:3,3]/=100.
    expectedposelocal[:3,3]/=100.
    expectedskin=expectedpose@np.linalg.inv(expectedref)
    row={'bone':name,'parent':r['parent'],
        'skeleton_reference_local':compare(matrix(ref['local']),expectedreflocal),
        'skeleton_reference_global':compare(reference,expectedref),'evaluations':{}}
    for label,evaluation in ue['evaluations'].items():
        p=evaluation[name]
        actual=matrix(p['global'])
        actualskin=actual@np.linalg.inv(matrix(p['reference_global']))
        row['evaluations'][label]={'local':compare(matrix(p['local']),expectedposelocal),
            'global':compare(actual,expectedpose),'skin':compare(actualskin,expectedskin),
            'vs_raw_local':compare(matrix(p['local']),matrix(ue['evaluations']['raw_unretargeted'][name]['local'])),
            'vs_raw_global':compare(actual,matrix(ue['evaluations']['raw_unretargeted'][name]['global']))}
    rows.append(row)
result={'source':str(OUT/'blender_capture_bones1152.json'),'ue':str(OUT/'ue_capture_bone_poses.json'),
    'compared_bones':len(rows),
    'reference_global_max_translation_error_cm':max(r['skeleton_reference_global']['translation_error_cm']for r in rows),
    'reference_global_largest_errors':sorted([(r['bone'],r['skeleton_reference_global'])for r in rows],key=lambda r:r[1]['translation_error_cm'],reverse=True)[:25],
    'evaluation_summary':{},'mesh_reference_summary':{},'rows':rows}
for label in ue['evaluations']:
    field='translation_error_cm'
    er=[(r['bone'],r['evaluations'][label])for r in rows]
    result['evaluation_summary'][label]={
        'maximum_local_translation_error_cm':max(r['local'][field]for n,r in er),
        'maximum_global_translation_error_cm':max(r['global'][field]for n,r in er),
        'maximum_global_linear_matrix_error':max(r['global']['linear_matrix_error']for n,r in er),
        'maximum_skin_translation_error_cm':max(r['skin'][field]for n,r in er),
        'maximum_skin_linear_matrix_error':max(r['skin']['linear_matrix_error']for n,r in er),
        'maximum_vs_raw_local_translation_error_cm':max(r['vs_raw_local'][field]for n,r in er),
        'maximum_vs_raw_global_translation_error_cm':max(r['vs_raw_global'][field]for n,r in er),
        'largest_global_errors':sorted([(n,r['global'])for n,r in er],key=lambda r:r[1][field],reverse=True)[:20],
        'largest_skin_errors':sorted([(n,r['skin'])for n,r in er],key=lambda r:r[1][field],reverse=True)[:20]}
for chunk,doc in ue['mesh_evaluations'].items():
    refrows=[]
    for n,p in doc['bones'].items():
        if n not in src:continue
        a=matrix(p['reference_global'])
        b=matrix(ue['skeleton_reference'][n]['global'])
        expectedref=np.array(src[n]['rest_global_ue_cm'])
        expectedref[:3,:3]*=100.
        refrows.append({'bone':n,'mesh_vs_skeleton_ref':compare(a,b),
            'mesh_vs_source_ref':compare(a,expectedref),
            'mesh_pose_vs_base_compressed':compare(matrix(p['global']),matrix(ue['evaluations']['compressed_retargeted'][n]['global']))})
    result['mesh_reference_summary'][chunk]={'bones':len(refrows),
        'mesh_vs_skeleton_ref_max_translation_cm':max(r['mesh_vs_skeleton_ref']['translation_error_cm']for r in refrows),
        'mesh_vs_skeleton_ref_max_linear_error':max(r['mesh_vs_skeleton_ref']['linear_matrix_error']for r in refrows),
        'mesh_vs_source_ref_max_translation_cm':max(r['mesh_vs_source_ref']['translation_error_cm']for r in refrows),
        'mesh_pose_vs_base_compressed_max_translation_cm':max(r['mesh_pose_vs_base_compressed']['translation_error_cm']for r in refrows),
        'largest_mesh_vs_skeleton_ref':sorted(refrows,key=lambda r:r['mesh_vs_skeleton_ref']['translation_error_cm'],reverse=True)[:15]}
(OUT/'bone_difference_analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:({a:{b:c for b,c in v.items()if not b.startswith('largest')}for a,v in value.items()}if k=='evaluation_summary'else value)for k,value in result.items()if k not in('rows','mesh_reference_summary','reference_global_largest_errors')},indent=2))
print('MESH_REF '+json.dumps({k:{a:b for a,b in v.items()if a!='largest_mesh_vs_skeleton_ref'}for k,v in result['mesh_reference_summary'].items()},indent=2))
