"""Preserve each clothing/prop PAK's original local skeleton and anchor map."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
from decode_model_viewer_static_pose import package_resources

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
SOURCE=Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97')
OUT=ROOT/'Exports/OriginalOwnedRigs'
C=np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]],float)


def sqt_matrix(s,q,t):
    x,y,z,w=np.asarray(q)/np.linalg.norm(q)
    r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    out=np.eye(4);out[:3,:3]=r@np.diag(s);out[:3,3]=t
    return out


def decode_owned(name):
    source=SOURCE/name;b=source.read_bytes();pages,resources,pointer=package_resources(b)
    r=next(r for r in resources if r['type']=='JOINT_HIERARCHY')
    x=pointer(r['address']+80,r['page']);name_table=pointer(r['address']+104,r['page'])
    if struct.unpack_from('<I',b,x)[0]!=0x41480105:raise ValueError('hierarchy magic')
    nodes,transforms=struct.unpack_from('<2H',b,x+16)
    header=struct.unpack_from('<I',b,x+32)[0];hr=struct.unpack_from('<I',b,x+60)[0]
    hbytes=struct.unpack_from('<I',b,x+hr+20)[0];parent_table=x+hr+hbytes
    parents=[struct.unpack_from('<4i',b,parent_table+16*i) for i in range(nodes)]
    names=[]
    for i in range(nodes):
        address=pointer(name_table+16*i+8,r['page']);names.append(b[address:b.index(0,address)].decode())
    def root_of(index):
        while parents[index][1]>=0:index=parents[index][1]
        return index
    transform_nodes=[i for i in range(nodes) if root_of(i)==0]
    if len(transform_nodes)!=transforms:raise ValueError('source transform mapping')
    source_transform={}
    for ti,bi in enumerate(transform_nodes):
        address=x+header+48*ti;v=struct.unpack_from('<12f',b,address)
        source_transform[bi]=dict(scale=list(v[:3]),rotation_xyzw=list(v[4:8]),translation=list(v[8:11]),source_absolute_offset=address)
    character=json.loads((ROOT/'Exports/Ellie_CorrectBindRest_SourceMatrices.json').read_text())['rows']
    by_name={r['bone_name']:r for r in character}
    suffixes=['_patrol_hoodie_cloth','_jacket_cloth','_seattle_hoodie_cloth','_patrol_hoodie_string_cloth','_seattle_hoodie_string_cloth']
    rows=[];globals=[];comparisons=[]
    for i,name in enumerate(names):
        sqt=source_transform.get(i)
        local=sqt_matrix(sqt['scale'],sqt['rotation_xyzw'],sqt['translation']) if sqt else np.eye(4)
        parent=parents[i][1]
        if parent>=i:raise ValueError('non-topological hierarchy')
        global_matrix=globals[parent]@local if parent>=0 else local;globals.append(global_matrix)
        stem=name
        for suffix in suffixes:
            if stem.endswith(suffix):stem=stem[:-len(suffix)];break
        anchor=by_name.get(stem)
        row=dict(bone_index=i,bone_name=name,parent_index=parent,original_parenting_row=list(parents[i]),source_local_sqt=sqt,
            local_matrix_game_meters=local.tolist(),global_matrix_game_meters=global_matrix.tolist(),
            global_matrix_blender_meters=(C@global_matrix@C.T).tolist(),
            ellie_anchor_candidate=dict(bone_index=anchor['bone_index'],bone_name=stem,source_reference_has_sqt=anchor['original_local_sqt_available']) if anchor else None,
            reference_policy='original source float32 S/Q/T' if sqt else 'explicit identity-local fallback for external/helper node')
        rows.append(row)
        if anchor and anchor['original_local_sqt_available']:
            err=float(np.max(abs(global_matrix-np.array(anchor['global_matrix_game_meters']))))
            comparisons.append(dict(owned_bone_index=i,anchor_bone_index=anchor['bone_index'],bone_name=stem,max_bind_global_error=err))
    return dict(source_package=str(source),source_sha256=hashlib.sha256(b).hexdigest(),resource_name=r['name'],hierarchy_absolute_offset=x,
        bone_count=nodes,original_sqt_count=transforms,rows=rows,primary_anchor_reference_comparisons=comparisons,
        policy='Skin indices in this PAK address this owned rig. They must never index the unrelated1074-node character rig directly. Anchor mappings are explicit candidates; simulation bones retain original names and source matrices.')


def main():
    OUT.mkdir(parents=True,exist_ok=True);summary=[]
    for name in ['ellie-patrol-hoodie-cloth.pak','backpack-ellie.pak','ellie-jacket-cloth-skel.pak','ellie-seattle-hoodie-cloth-skel.pak']:
        d=decode_owned(name);target=OUT/(name.replace('.pak','.json'));target.write_text(json.dumps(d,indent=2))
        summary.append(dict(source=name,path=str(target),bones=d['bone_count'],original_sqt=d['original_sqt_count'],anchor_candidates=sum(r['ellie_anchor_candidate']is not None for r in d['rows']),primary_anchor_comparisons=d['primary_anchor_reference_comparisons']))
    (OUT/'owned_rig_inventory.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
