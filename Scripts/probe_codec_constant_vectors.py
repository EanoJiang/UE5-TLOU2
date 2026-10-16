"""Decode bounded const float16 vectors and compare known bone-local offsets.

The 0x0316 op data is destination u16[count] followed by float16 vec3[count].
This exports actual constant vectors, preserving source units, and tests the
target's A/main and B/finger destinations against extracted local matrices.
The compare is evidence for a partial section map, never a full animation.
"""
import json, struct, math, hashlib
from pathlib import Path

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
PAK=Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
CAP=ROOT/'Exports/ExactDebug/ellie16_patrol_body/capture.json'
OUT=ROOT/'Content/TLOU2/Reports'

def main():
    blob=PAK.read_bytes()[0x95ae20:0x95ae20+0x9c0]
    bones=json.loads(CAP.read_text(encoding='utf-8'))['bones']
    tables=[]
    for name,section,offset,n,count,base in [('A_main',0x120,0x160,16,127,0),('B_fingers',0x2b0,0x2d0,40,38,322)]:
        # Verify the source op header before decoding its bounded output array.
        opcode,opcount,opaux,relative=struct.unpack_from('<4H',blob,section)
        assert opcode==0x316 and opcount==n and section+relative==offset
        dst=list(struct.unpack_from('<'+str(n)+'H',blob,offset))
        data=offset+2*n
        rows=[]
        for i,v in enumerate(dst):
            triple=list(struct.unpack_from('<3e',blob,data+6*i))
            local=v//48;component=v%48;sentinel=v==48*count
            index=base+local if not sentinel else None
            row={'entry':i,'destination':f'0x{v:x}','local_record':local,
                 'component_offset':component,'sentinel':sentinel,'half_values':triple,
                 'candidate_bone_index':index,
                 'candidate_bone_name':bones[index]['name'] if index is not None else None}
            if not sentinel and component==32:
                original=bones[index]['matrix'][3][:3]
                converted=[x*.01 for x in original]
                err=[abs(a-b) for a,b in zip(converted,triple)]
                row.update(capture_local_translation=original,
                           capture_translation_scaled_0_01=converted,
                           max_absolute_error=max(err),
                           translation_matches_half_precision=max(err)<0.00015)
            elif not sentinel and component==0:
                row['is_unit_scale']=triple==[1.0,1.0,1.0]
            rows.append(row)
        translations=[r for r in rows if r['component_offset']==32 and not r['sentinel']]
        tables.append({'name':name,'section':f'0x{section:x}','opcode':'0x0316',
                       'count':n,'output_offset':f'0x{offset:x}',
                       'value_offset':f'0x{data:x}','candidate_section_bone_base':base,
                       'translation_rows':len(translations),
                       'translation_matches':sum(r['translation_matches_half_precision'] for r in translations),
                       'rows':rows})
    doc={'tool':'probe_codec_constant_vectors.py','status':'bounded_float16_const_vectors_and_partial_bone_map_evidence',
         'payload_sha256':hashlib.sha256(blob).hexdigest(),'tables':tables,
         'observations':[
             'Opcode 0x0316 uses u16 destination offsets followed by count float16 vec3 values; its relative-data pointers resolve exactly.',
             'Component offset 0 carries unit scale triples in both tables; component offset 32 carries local translation triples.',
             'B/fingers local records 1,3,...37 map to extracted bone indices 323,325,...359 (base322), matching all19 local translations at 0.01 scale within half precision.',
             'A/main local records32,34,36,38,42,44 match the corresponding extracted bone translations at 0.01 scale. Hand-prop slot40 uses clip-specific data and are retained without forcing a match.',
             'This establishes a plausible partial group-to-bone map grounded in actual translation vectors. Dynamic quaternion decoding and original whole-body pose reconstruction remain unresolved.',
         ]}
    (OUT/'CODEC_41430102_CONSTANT_VECTOR_EVIDENCE.json').write_text(json.dumps(doc,indent=2),encoding='utf-8')
    lines=['# 0x41430102 bounded constant-vector decode and bone-map evidence','',
           'The `0x0316` records resolve to a u16 destination array followed by float16 vec3 values. These are actual decoded constant vectors, with destination slots and source units preserved.','',
           '| Section | Output count | Translation rows | Match capture local translation x0.01 | Candidate bone base |',
           '|---|---:|---:|---:|---:|']
    for t in tables:lines.append(f"| `{t['name']}` | {t['count']} | {t['translation_rows']} | {t['translation_matches']} | {t['candidate_section_bone_base']} |")
    lines+=['','## Evidence interpretation','',*['- '+x for x in doc['observations']], '',
            'The JSON records every raw half vector, destination, candidate bone, and residual against the extracted local matrix. This is a partial static-channel decode; it is not a full original animation or a UE-validated transform reconstruction.']
    (OUT/'CODEC_41430102_CONSTANT_VECTOR_EVIDENCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'tables':[{'name':t['name'],'translations':t['translation_rows'],'matches':t['translation_matches']} for t in tables]},indent=2))

if __name__=='__main__':main()
