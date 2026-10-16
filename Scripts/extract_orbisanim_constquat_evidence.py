"""Reproduce the located shipped-code evidence for constant q48 decoding."""
import json, struct, hashlib
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64, x86_const

EXE=Path(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe')
OUT=Path(r'D:/TLOU2_UE5_8_Codex/Content/TLOU2/Reports')

def main():
    blob=EXE.read_bytes();pe=pefile.PE(data=blob,fast_load=True)
    start,end=0x218ec20,0x218f045
    a,z=pe.get_offset_from_rva(start),pe.get_offset_from_rva(end)
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    insns=list(md.disasm(blob[a:z],pe.OPTIONAL_HEADER.ImageBase+start))
    rows=[]
    for i in insns:
        for op in i.operands:
            if op.type!=3 or op.mem.base!=x86_const.X86_REG_RIP:continue
            target=i.address+i.size+op.mem.disp
            try:o=pe.get_offset_from_rva(target-pe.OPTIONAL_HEADER.ImageBase);data=blob[o:o+16]
            except:continue
            if len(data)!=16:continue
            rows.append({'instruction':hex(i.address),'mnemonic':i.mnemonic,'operand':i.op_str,
                         'target':hex(target),'file_offset':hex(o),
                         'u32':[hex(x) for x in struct.unpack('<4I',data)],
                         'f32':list(struct.unpack('<4f',data))})
    doc={'tool':'extract_orbisanim_constquat_evidence.py','executable':str(EXE),
         'sha256':hashlib.sha256(blob).hexdigest(),'rva_range':[hex(start),hex(end)],
         'file_range':[hex(a),hex(z)],'function_sha256':hashlib.sha256(blob[a:z]).hexdigest(),
         'rip_constants':rows,
         'verified_operations':['Low2 bits select the output permutation.',
           'The raw high32 word is masked0xffff, converted to float, multiplied by sqrt(1/2)/32768, biased by -sqrt(1/2).',
           'Two other components are read by shifting the u64 right17 and right2, masked0x7fff, converted to float, multiplied by sqrt(1/2)/16384, biased by -sqrt(1/2).',
           'The missing component is reconstructed as positive sqrt(1-sum(three components squared)); the SIMD path clamps the residual to FLT_MIN.',
           'The reconstructed four-vector is permuted using a low2-bit selected control table.'],
         'boundary':'This is direct executable instruction evidence for q48 constant data. Original dynamic compressed stream and skeleton section mapping still require separate validation.'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'CONST_QUAT48_EXECUTABLE_EVIDENCE.json').write_text(json.dumps(doc,indent=2),encoding='utf-8')
    (OUT/'CONST_QUAT48_EXECUTABLE_DISASSEMBLY.txt').write_text('\n'.join(f'{i.address:016x} {i.mnemonic} {i.op_str}' for i in insns)+'\n',encoding='utf-8')
    (OUT/'CONST_QUAT48_EXECUTABLE_CONSTANTS.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(json.dumps({'rva':[hex(start),hex(end)],'constants':len(rows),'sha256':doc['function_sha256']},indent=2))

if __name__=='__main__':main()
