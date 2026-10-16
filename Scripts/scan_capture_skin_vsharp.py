"""Find captured deformer CBVs by exact paired matrix VSharp grammar.

The scan targets UID7556's original contiguous upload pages. Findings retain
their buffer offsets and matrix palette offsets, not guessed skeleton names.
"""
from pathlib import Path
import sys,json,struct
import numpy as np
from ngfx_resource_reader import resource_pages,read_chunk,read_resource

ROOT=Path(r'D:/TLOU2_UE5_8_Codex');CAP=ROOT/'Exports/CaptureBuffers'
COUNTS={16,20,22,30,75,78,86,1038,1074,238}

def main():
    pages=resource_pages(7556);resource_size=sum(p['bytes'] for p in pages);rows=[]
    for page in pages:
        data=read_chunk(page['chunk_id'])[page['chunk_offset']:page['chunk_offset']+page['bytes']]
        v=np.frombuffer(data[:len(data)//16*16],dtype='<u4').reshape(-1,4)
        count=v[:-3,3];second=v[3:,3]
        mask=(((v[:-3,1]&0xffff0000)==0x10000000)&((v[:-3,1]&0xffff)<1000)&(v[:-3,2]==0)&(count>=3)&(count<=6000)&(count%3==0)
            &((v[3:,1]&0xffff0000)==0x10000000)&((v[3:,1]&0xffff)<1000)&(v[3:,2]==0)&(count==second)
            &(v[:-3,0].astype(np.uint64)*16+count.astype(np.uint64)*16<=resource_size)
            &(v[3:,0].astype(np.uint64)*16+count.astype(np.uint64)*16<=resource_size))
        for i in np.flatnonzero(mask):
            i=int(i);offset=page['resource_offset']+16*i;num=int(v[i,3])//3
            data=read_resource(7556,offset,528)
            descriptors=[list(struct.unpack_from('<4I',data,48*j)) for j in range(11)]
            if offset%256:continue
            row={'resource_uid':7556,'cbv_resource_offset':offset,'cbv_alignment256':offset%256==0,
                'source_chunk_id':page['chunk_id'],'source_chunk_offset':16*i+page['chunk_offset'],
                'matrix_count':num,'palette_buffer_table_index':int(v[i,1])&65535,'palette_resource_offset':int(v[i,0])*16,
                'second_palette_buffer_table_index':int(v[i+3,1])&65535,
                'second_palette_resource_offset':int(v[i+3,0])*16,'matrix_vsharp_y':int(v[i,1]),
                'vsharp_descriptors':descriptors,'source_vertex_count':descriptors[2][3]&524287}
            rows.append(row)
    rows.sort(key=lambda r:r['cbv_resource_offset'])
    result={'resource_uid':7556,'resource_bytes':resource_size,'candidate_count':len(rows),'counts':{str(n):sum(r['matrix_count']==n for r in rows) for n in sorted(set(r['matrix_count'] for r in rows))},'rows':rows,
        'scope':'Paired current/second matrix VSharp metadata read from captured initial upload bytes; actual dispatch association and garment joint order require separate validation.'}
    path=CAP/'skin_vsharp_candidates.json';path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(path),'counts':result['counts'],'candidate_count':len(rows),'hoodie_pointer_matches':[{k:r[k] for k in ['cbv_resource_offset','matrix_count','palette_resource_offset','source_vertex_count']} for r in rows if r['palette_resource_offset']==136907840]},indent=2))

if __name__=='__main__':main()
