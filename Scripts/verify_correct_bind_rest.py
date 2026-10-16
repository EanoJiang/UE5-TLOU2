"""Independent original-byte and parent-matrix validation for corrected rest."""
import json
import struct
from pathlib import Path
import numpy as np

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')


def qmat(q):
    x,y,z,w=q;k=2/(x*x+y*y+z*z+w*w)
    return np.array([[1-k*(y*y+z*z),k*(x*y-z*w),k*(x*z+y*w)],
                     [k*(x*y+z*w),1-k*(x*x+z*z),k*(y*z-x*w)],
                     [k*(x*z-y*w),k*(y*z+x*w),1-k*(x*x+y*y)]])


def main():
    path=ROOT/'Exports/Ellie_CorrectBindRest_SourceMatrices.json'
    rows=json.loads(path.read_text())['rows']
    raw=(ROOT/'Content/TLOU2/SourcePaks/ellie-skel.pak').read_bytes()
    basis=np.array([[1.,0,0,0],[0,0,-1.,0],[0,1.,0,0],[0,0,0,1.]])
    source_errors=[];parent_errors=[];basis_errors=[];det_errors=[];primary=0;fallback=0
    for row in rows:
        local=np.array(row['local_matrix_game_meters'])
        global_mat=np.array(row['global_matrix_game_meters'])
        converted=np.array(row['global_matrix_blender_meters'])
        parent=row['parent_index']
        expected=np.array(rows[parent]['global_matrix_game_meters'])@local if parent>=0 else local
        parent_errors.append(float(np.max(np.abs(global_mat-expected))))
        basis_errors.append(float(np.max(np.abs(converted-basis@global_mat@basis.T))))
        det_errors.append(float(abs(np.linalg.det(global_mat[:3,:3])-1)))
        if row['original_local_sqt_available']:
            primary+=1
            v=struct.unpack_from('<12f',raw,row['source_local_sqt']['source_absolute_offset'])
            expected=np.eye(4);expected[:3,:3]=qmat(v[4:8])@np.diag(v[:3]);expected[:3,3]=v[8:11]
            source_errors.append(float(np.max(np.abs(local-expected))))
        else:
            fallback+=1
            if not np.array_equal(local,np.eye(4)):raise ValueError('helper fallback not identity')
    root_t=np.array(rows[0]['global_matrix_blender_meters'])[:3,3].tolist()
    checks={
        'rows1074_unique':len(rows)==1074 and len(set(r['bone_index'] for r in rows))==1074,
        'raw_original520_reference':primary==520,'procedural554_fallback_explicit':fallback==554,
        'source_local_matrix_bytes_match':max(source_errors)==0.,
        'parent_accumulation_exact':max(parent_errors)==0.,'basis_conjugation_exact':max(basis_errors)==0.,
        'unit_rotation_determinants':max(det_errors)<1e-10,
        'root_meter_position':max(abs(a-b) for a,b in zip(root_t,[0.,-.00986884068697691,.9454938173294067]))<1e-12,
        'main_tail16_original_rest_retained':all(rows[i]['original_local_sqt_available'] for i in range(127,143)),
    }
    out={'source':str(path),'checks':checks,'pass':all(checks.values()),
         'root_global_blender_translation_meters':root_t,
         'max_source_local_matrix_error':max(source_errors),'max_parent_matrix_error':max(parent_errors),
         'max_basis_matrix_error':max(basis_errors),'max_rotation_determinant_error':max(det_errors),
         'non_driven570_policy':{'main_tail16':'bones127..142 retain original float32 S/Q/T reference',
                               'procedural554':'explicit identity-local parent-inheritance fallback; original runtime constraint solve not reproduced'}}
    report=ROOT/'Exports/correct_bind_rest_independent_validation.json'
    report.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
    if not out['pass']:raise SystemExit(1)


if __name__=='__main__':main()
