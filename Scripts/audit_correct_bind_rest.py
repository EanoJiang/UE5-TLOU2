"""Export original S/Q/T local and accumulated global bind matrices in meters."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from decode_bindpose_static_sections import read_skeleton_reference

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')


def quat_matrix(q,t,s):
    x,y,z,w=map(float,q)
    k=2.0/(x*x+y*y+z*z+w*w)
    m=np.array([[1-k*(y*y+z*z),k*(x*y-z*w),k*(x*z+y*w),t[0]],
                [k*(x*y+z*w),1-k*(x*x+z*z),k*(y*z-x*w),t[1]],
                [k*(x*z-y*w),k*(y*z+x*w),1-k*(x*x+y*y),t[2]],
                [0.,0.,0.,1.]],dtype=np.float64)
    return m@np.diag([*s,1.])


def main():
    reference=read_skeleton_reference()
    bones=json.loads((ROOT/'Exports/ExactDebug/ellie16_patrol_body/capture.json').read_text())['bones']
    basis=np.array([[1.,0.,0.,0.],[0.,0.,-1.,0.],[0.,1.,0.,0.],[0.,0.,0.,1.]])
    global_game={}
    rows=[]
    for bi,bone in enumerate(bones):
        parent=bone['parentIndex']
        parent_global=global_game.get(parent,np.eye(4))
        ref=reference['transforms'].get(bi)
        if ref:
            local=quat_matrix(ref['rotation'],ref['translation'],ref['scale'])
            verified=True
            policy='original float32 local S/Q/T accumulated through original parents'
        else:
            # Procedural/helper nodes have no original S/Q/T record. This fallback
            # is clearly tagged; it is not reconstructed game constraint output.
            local=np.eye(4)
            verified=False
            policy='procedural helper fallback: identity local transform, inherits parent; original constraint output unavailable'
        global_matrix=parent_global@local
        global_game[bi]=global_matrix
        converted=basis@global_matrix@basis.T
        rows.append({'bone_index':bi,'bone_name':bone['name'],'parent_index':parent,
                     'original_local_sqt_available':verified,'reference_policy':policy,
                     'source_local_sqt':ref,'local_matrix_game_meters':local.tolist(),
                     'global_matrix_game_meters':global_matrix.tolist(),
                     'global_matrix_blender_meters':converted.tolist(),
                     'old_export_head_from_capture_local_cm':bone['matrix'][3][:3]})
    verts=[]
    caproot=ROOT/'Exports/ExactDebug'
    folders=['ellie16_patrol_body','ellie_patrol_jacket','ellie_patrol_hoodie_cloth','ellie_patrol_pants','ellie_patrol_boots','ellie_patrol_hair','backpack_ellie','ellie_head','ellie_patrol_l_glove','ellie_patrol_r_glove']
    for name in folders:
        folder=caproot/name
        cap=json.loads((folder/'capture.json').read_text())
        for item in cap['meshes']:
            z=np.load(folder/item['npz'])
            stride=item['bindings']['pos']['stride']//4
            a=np.frombuffer(z['pos_raw'].tobytes(),dtype='<f4').reshape(-1,stride)[:item['vertex_count'],:3]
            verts.append(a)
    positions=np.concatenate(verts)
    primary_positions=np.array([r['global_matrix_game_meters'] for r in rows if r['original_local_sqt_available']])[:,:3,3]
    out={'tool':Path(__file__).name,'unit':'meters','vector_convention':'column vectors; global=parent_global@local; Blender basis conjugation C@M@C.T with C(x,y,z)=(x,-z,y)',
         'original_sqt_bones':520,'procedural_helper_fallback_bones':554,
         'geometry_bounds_game_meters':{'min':positions.min(axis=0).tolist(),'max':positions.max(axis=0).tolist()},
         'primary_global_bone_bounds_game_meters':{'min':primary_positions.min(axis=0).tolist(),'max':primary_positions.max(axis=0).tolist()},
         'old_export_issues':['capture.json local translation was scaled100 by Noesis while raw mesh positions stayed meters','make_armature treated local positions as global heads','make_armature discarded original bone rotations'],
         'rows':rows}
    path=ROOT/'Exports/Ellie_CorrectBindRest_SourceMatrices.json'
    path.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(path),'primary_bones':520,'helper_fallback_bones':554,'geometry_bounds':out['geometry_bounds_game_meters'],'primary_global_bounds':out['primary_global_bone_bounds_game_meters']},indent=2))


if __name__=='__main__':main()
