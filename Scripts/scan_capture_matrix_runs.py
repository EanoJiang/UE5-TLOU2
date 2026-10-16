"""Find candidate float32 3x4 matrix palettes in recovered GPU data chunks.

Candidates are a search aid, not a claimed bone assignment. Actual shader
bindings and original skeleton comparisons are required to establish meaning.
"""
from pathlib import Path
import json,time
import numpy as np

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
CAP=ROOT/'Exports/CaptureBuffers'

def find_runs(data,minimum=8):
    vector=np.frombuffer(data[:len(data)//16*16],dtype='<f4').reshape(-1,4)
    if len(vector)<3*minimum:return []
    a,b,c=vector[:-2,:3],vector[1:-1,:3],vector[2:,:3]
    with np.errstate(over='ignore',invalid='ignore'):
        norm=np.sum(vector[:,:3]*vector[:,:3],axis=1)
        valid=((np.abs(norm[:-2]-1)<0.035)&(np.abs(norm[1:-1]-1)<0.035)&(np.abs(norm[2:]-1)<0.035)
           &(np.abs(np.sum(a*b,axis=1))<0.025)&(np.abs(np.sum(a*c,axis=1))<0.025)&(np.abs(np.sum(b*c,axis=1))<0.025)
           &(np.max(np.abs(vector[:-2,3:4]),axis=1)<10000)&(np.max(np.abs(vector[1:-1,3:4]),axis=1)<10000)&(np.max(np.abs(vector[2:,3:4]),axis=1)<10000))
    output=[]
    for phase in range(3):
        values=valid[phase::3]
        changes=np.flatnonzero(np.diff(np.r_[False,values,False].astype(np.int8)))
        for first,last in zip(changes[::2],changes[1::2]):
            count=int(last-first)
            if count<minimum:continue
            start=(phase+int(first)*3)*16
            matrices=vector[phase+int(first)*3:phase+int(last)*3].reshape(-1,3,4)
            variation=float(np.max(np.ptp(matrices,axis=0)))
            if variation<1e-5:continue
            output.append({'byte_offset':start,'matrix_count':count,'byte_count':count*48,
                'max_component_variation':variation,'translation_min_xyz':matrices[:,:,3].min(axis=0).tolist(),
                'translation_max_xyz':matrices[:,:,3].max(axis=0).tolist(),'first_matrix_rows':matrices[0].tolist()})
    return output

def main():
    index=json.loads((CAP/'chunk_index.json').read_text(encoding='utf-8'));rows=[];start=time.time();scanned=0
    for record in index['records']:
        if record['decoded_bytes']<1152 or record['chunk_id']>=47211:continue
        data=Path(record['path']).read_bytes();scanned+=len(data)
        found=find_runs(data)
        for candidate in found:rows.append({'chunk_id':record['chunk_id'],'path':record['path'],**candidate})
        if record['chunk_id']%5000==0:print(json.dumps({'chunk_id':record['chunk_id'],'scanned_bytes':scanned,'candidates':len(rows),'seconds':round(time.time()-start,1)}),flush=True)
    rows.sort(key=lambda row:row['matrix_count'],reverse=True)
    result={'candidate_count':len(rows),'scanned_bytes':scanned,'rows':rows,
        'scope':'Candidate float32 3x4 matrices with near-orthonormal rotation and nonconstant values; no bone or resource UID assignment is inferred.'}
    path=CAP/'matrix_run_candidates.json';path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(path),'candidates':len(rows),'scanned_bytes':scanned,'seconds':round(time.time()-start,1),'largest':rows[:8]},indent=2))

if __name__=='__main__':main()
