"""Bounded executable evidence for OrbisAnim PostQuatLog and target dispatch.

Does not execute the game. Produces instruction listing, exact RIP constants,
and the target opcode/pointer grammar for independent native-oracle review.
"""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86 import X86_OP_MEM,X86_REG_RIP

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
EXE=Path(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe')
REPORTS=ROOT/'Content/TLOU2/Reports'
PAYLOAD=ROOT/'Exports/AnimationSources/DecodedRawChannels/codec_evidence/ellie-prone-lg-aim-strafe-0-fw_41430102_payload.ndanim.bin'

def main():
    data=EXE.read_bytes();pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
    functions=[];lines=[]
    for name,start,end in [('post_quat_log_two_frames',0x2196b00,0x2196d70),('post_quat_log_single_frame',0x2196d70,0x2196f8c),('post_quat_log_pca_two_frames',0x2196f90,0x2197230),('post_quat_log_pca_single_frame',0x2197230,0x2197433)]:
        code=data[pe.get_offset_from_rva(start):pe.get_offset_from_rva(end)]
        instructions=list(md.disasm(code,base+start));constants=[];calls=[]
        lines.append(f'FUNCTION {name} RVA {start:#x}..{end:#x}')
        for i in instructions:
            lines.append(f'{i.address:016x} {i.mnemonic} {i.op_str}')
            if i.mnemonic=='call':calls.append(i.op_str)
            for op in i.operands:
                if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
                    rva=i.address+i.size+op.mem.disp-base
                    raw=pe.get_offset_from_rva(rva);payload=data[raw:raw+16]
                    constants.append({'instruction_rva':hex(i.address-base),'target_rva':hex(rva),'raw_offset':hex(raw),'hex':payload.hex(),'float4':list(struct.unpack('<4f',payload))})
        functions.append({'name':name,'rva':hex(start),'end_rva':hex(end),'sha256':hashlib.sha256(code).hexdigest(),'calls':calls,'rip_constants':constants})
    blob=PAYLOAD.read_bytes();ops=[];p=0x120
    while p<0x160:
        op=struct.unpack_from('<H',blob,p)[0]
        if not op:break
        n=op>>8;args=list(struct.unpack_from('<'+'H'*n,blob,p+2))
        ops.append({'offset':hex(p),'opcode':hex(op),'argument_count':n,'arguments':args})
        p+=2*(n+1)
    meta=[]
    for pair in range(2):
        shorts=struct.unpack_from('<8h',blob,0x270+16*pair)
        meta.append({'payload_offset':hex(0x270+16*pair),'signed_shorts':list(shorts),'track_even_snorm16_xyzw':[shorts[2*i]/32768 for i in range(4)],'track_odd_snorm16_xyzw':[shorts[2*i+1]/32768 for i in range(4)]})
    table=[]
    for table_rva,kind in [(0x38490e0,'two_frame'),(0x3849108,'single_frame')]:
        for opcode in range(0x1a,0x1f):
            rva=table_rva+opcode*8;raw=pe.get_offset_from_rva(rva)
            table.append({'table_kind':kind,'opcode':hex(opcode),'raw_offset':hex(raw),'rva':hex(rva),'function_va':hex(struct.unpack_from('<Q',data,raw)[0])})
    dispatcher_code=data[pe.get_offset_from_rva(0x219e700):pe.get_offset_from_rva(0x219e9e2)]
    lines.append('DYNAMIC OPCODE DISPATCH RVA 0x219e700..0x219e9e2')
    for i in md.disasm(dispatcher_code,base+0x219e700):lines.append(f'{i.address:016x} {i.mnemonic} {i.op_str}')
    result={'executable':str(EXE),'payload':str(PAYLOAD),'functions':functions,'dynamic_function_table':table,'target_section_a_operations':ops,'target_post_log_metadata':meta,
      'interpretation':{'header_high_byte':'number of u16 arguments after opcode','op_0x060b':'bit unpack, widths section+0xf0 = 0x210, scratch 0, stride 15','op_0x041b':'3VecRange, metadata section+0x100 = 0x220','op_0x041d':'PostQuatLog, metadata section+0x150 = 0x270','op_0x0410':'scatter float4, destinations section+0x170 = 0x290','single_frame_post_log_signature':'void(uint16 count, void* inout_float4, size_t stride, void* packed_snorm16_basequat_pairs)','native_post_log_rva':'0x2196d70','target_count':4,'target_stride':16,'no_external_calls':not functions[1]['calls'],
      'dispatch_proof':'RVA 0x219e798 subtracts opcode low byte 0x1a and bounds through 0x1e. RVA 0x219e879 and 0x219e8a7 call table 0x3849108 + opcode*8 for single-frame flags, while RVA 0x219e7fa uses table 0x38490e0 for dual-frame flags. Table low-byte0x1b resolves Range0x21902d0, low-byte0x1d resolves PostLog0x2196d70. Thus the target uses PostLog, not PostLogPca0x1e.',
      'limit':'Direct executable arithmetic, bounded opcode dispatch, and target payload pointers are documented. Full animation semantics also need section palette and destination mapping validation.'}}
    (REPORTS/'POST_QUAT_LOG_EXECUTABLE_EVIDENCE.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (REPORTS/'POST_QUAT_LOG_EXECUTABLE_DISASSEMBLY.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'functions':[{k:f[k] for k in ['name','rva','calls','sha256']} for f in functions],'ops':ops,'meta':meta},indent=2))

if __name__=='__main__':main()
