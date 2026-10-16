"""Independent isolated native checks of the source gallery constant decoder."""
import ctypes as C
import json
import struct
from pathlib import Path
from native_orbis_leaf_probe import load_image

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/AnimationSources/DecodedOriginal'


def main():
    base=load_image()
    signature=C.WINFUNCTYPE(None,C.c_uint16,C.c_void_p,C.c_void_p,C.c_void_p)
    functions={0x315:signature(base+0x218e9f0),0x316:signature(base+0x218e760),
               0x318:signature(base+0x218f050),0x319:signature(base+0x218eb60)}
    report=[]
    for name in ['model-viewer-ellie-patrol','model-viewer-ellie-16-patrol','model-viewer-ellie','model-viewer-ellie-seattle']:
        doc=json.loads((OUT/(name+'.json')).read_text());blob=(OUT/(name+'.ndanim.bin')).read_bytes()
        tracks={t['bone_index']:t for t in doc['tracks']};scalar={s['parameter_index']:s['value'] for s in doc['scalar_parameters']}
        compared={hex(op):0 for op in functions};exact={hex(op):0 for op in functions};maximum={hex(op):0.0 for op in functions};groups=[]
        for section in doc['operation_programs']:
            for op in section['operations']:
                opcode=int(op['opcode'],16);key=hex(opcode);count=op['padded_count'];active=op['active_count']
                table=C.create_string_buffer(struct.pack('<'+'H'*count,*op['destinations']))
                width=12 if opcode==0x315 else 4 if opcode==0x319 else 6
                # Native leaves process eight lanes; padded sentinel lanes may
                # read the next source bytes but write only an owned dummy slot.
                data=C.create_string_buffer(blob[op['data']:op['data']+count*width]+bytes(128))
                output=C.create_string_buffer(max(op['destinations'])+256)
                functions[opcode](count,C.addressof(output),C.addressof(data),C.addressof(table))
                for dest in op['destinations'][:active]:
                    if opcode==0x319:
                        expected=[scalar[dest//4]];actual=list(struct.unpack_from('<f',output.raw,dest))
                    else:
                        local,slot=divmod(dest,48);t=tracks[section['bone_base']+local]
                        expected=t['rotations_xyzw'][0] if opcode==0x318 else t['scale'] if slot==0 else t['translation']
                        actual=list(struct.unpack_from('<4f' if opcode==0x318 else '<3f',output.raw,dest))
                    err=max(abs(a-b) for a,b in zip(expected,actual));maximum[key]=max(maximum[key],err)
                    compared[key]+=len(expected)
                    exact[key]+=sum(struct.pack('<f',a)==struct.pack('<f',b) for a,b in zip(expected,actual))
                groups.append(dict(section=section['section_index'],opcode=key,count=count,active=active))
        passed=all(exact[k]==compared[k] for k in ['0x315','0x316','0x319']) and maximum['0x318']<1e-5
        report.append(dict(clip=name,compared_scalars=compared,bit_exact_scalars=exact,max_absolute_error=maximum,pass_=passed,groups=groups))
    result=dict(pass_=all(r['pass_'] for r in report),clips=report,native_leaves={hex(k):hex(v) for k,v in {0x315:0x218e9f0,0x316:0x218e760,0x318:0x218f050,0x319:0x218eb60}.items()},
        native_scope='Bounded no-external-call math leaves in isolated child Python; original PE entry point is never run. Float3/half3/scalar output must match IEEE32 bits exactly; Quat48 portable exact sqrt tolerates native approximate SIMD sqrt rounding.')
    output=ROOT/'Content/TLOU2/Reports/MODEL_VIEWER_NATIVE_CONSTANT_VERIFICATION.json'
    output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if not result['pass_']:raise SystemExit(1)


if __name__=='__main__':main()
