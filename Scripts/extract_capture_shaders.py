"""Extract exact DXBC/DXIL containers and disassemble with installed DXC.

This only parses bytecode; it does not execute GPU programs. Chunk IDs retain
container provenance and need separate PSO/resource binding association.
"""
from pathlib import Path
import ctypes as C,json,struct,uuid,hashlib,re

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
CAP=ROOT/'Exports/CaptureBuffers'
DLL=Path(r'C:/Program Files/NVIDIA Corporation/Nsight Graphics 2026.3.1/host/windows-desktop-nomad-x64/dxcompiler.dll')
HRESULT=C.c_long
class GUID(C.Structure):_fields_=[('data',C.c_ubyte*16)]
def guid(text):return GUID((C.c_ubyte*16).from_buffer_copy(uuid.UUID(text).bytes_le))
class DxcBuffer(C.Structure):_fields_=[('Ptr',C.c_void_p),('Size',C.c_size_t),('Encoding',C.c_uint32)]
def method(obj,slot,result,*args):
    table=C.cast(obj,C.POINTER(C.POINTER(C.c_void_p))).contents
    return C.WINFUNCTYPE(result,C.c_void_p,*args)(table[slot])

def disassemble(data,compiler):
    binary=C.create_string_buffer(data);source=DxcBuffer(C.addressof(binary),len(data),0);result=C.c_void_p()
    iid=guid('58346cda-dde7-4497-9461-6f87af5e0659')
    status=method(compiler,4,HRESULT,C.POINTER(DxcBuffer),C.POINTER(GUID),C.POINTER(C.c_void_p))(compiler,C.byref(source),C.byref(iid),C.byref(result))
    if status<0:return None,f'DisassembleHRESULT {status:#x}'
    try:
        outcome=HRESULT();method(result,3,HRESULT,C.POINTER(HRESULT))(result,C.byref(outcome))
        blob=C.c_void_p();get=method(result,4,HRESULT,C.POINTER(C.c_void_p))(result,C.byref(blob))
        if get<0 or not blob:return None,f'GetResultHRESULT {get:#x},status{outcome.value:#x}'
        try:
            pointer=method(blob,3,C.c_void_p)(blob);size=method(blob,4,C.c_size_t)(blob)
            return C.string_at(pointer,size).decode('utf-8','replace').rstrip('\0'),None
        finally:method(blob,2,C.c_ulong)(blob)
    finally:method(result,2,C.c_ulong)(result)

def disassemble_legacy(data):
    lib=C.WinDLL(str(DLL.parent/'d3dcompiler_47.dll'));fn=lib.D3DDisassemble
    fn.argtypes=[C.c_void_p,C.c_size_t,C.c_uint32,C.c_char_p,C.POINTER(C.c_void_p)];fn.restype=HRESULT
    binary=C.create_string_buffer(data);blob=C.c_void_p();status=fn(C.addressof(binary),len(data),0,None,C.byref(blob))
    if status<0:return None,f'D3DDisassembleHRESULT {status:#x}'
    try:
        pointer=method(blob,3,C.c_void_p)(blob);size=method(blob,4,C.c_size_t)(blob)
        return C.string_at(pointer,size).decode('utf-8','replace').rstrip('\0'),None
    finally:method(blob,2,C.c_ulong)(blob)

def parse_root_signature(data):
    part_offset=struct.unpack_from('<I',data,32)[0]
    tag,size=struct.unpack_from('<4sI',data,part_offset)
    if tag!=b'RTS0':raise ValueError('root signature missing RTS0')
    blob=data[part_offset+8:part_offset+8+size]
    version,count,params_offset,sampler_count,samplers_offset,flags=struct.unpack_from('<6I',blob)
    if version not in(1,2):raise ValueError(('root signature version',version))
    if params_offset+12*count>len(blob):raise ValueError('root parameter table bounds')
    parameters=[]
    for i in range(count):
        kind,visibility,offset=struct.unpack_from('<3I',blob,params_offset+12*i)
        parameter={'root_parameter':i,'type':kind,'visibility':visibility,'payload_offset':offset}
        if kind==0:
            nr,ro=struct.unpack_from('<2I',blob,offset);stride=24 if version==2 else 20
            if ro+stride*nr>len(blob):raise ValueError('root descriptor range bounds')
            ranges=[]
            for j in range(nr):
                values=struct.unpack_from('<'+'I'*(stride//4),blob,ro+stride*j)
                rt,n,reg,space=values[:4];rf,table_offset=(values[4],values[5]) if version==2 else(0,values[4])
                ranges.append({'type':{0:'SRV',1:'UAV',2:'CBV',3:'Sampler'}.get(rt,str(rt)),
                    'count':n,'base_shader_register':reg,'register_space':space,'flags':rf,'table_offset':table_offset})
            parameter['ranges']=ranges
        elif kind==1:
            register,space,words=struct.unpack_from('<3I',blob,offset)
            parameter.update({'shader_register':register,'register_space':space,'num32bit_values':words})
        elif kind in(2,3,4):
            register,space=struct.unpack_from('<2I',blob,offset)
            parameter.update({'shader_register':register,'register_space':space})
        else:raise ValueError(('root parameter type',kind))
        parameters.append(parameter)
    return {'serialized_version':version,'flags':flags,'static_sampler_count':sampler_count,'parameters':parameters}

def main():
    C.windll.kernel32.SetDllDirectoryW(str(DLL.parent));lib=C.WinDLL(str(DLL))
    create=lib.DxcCreateInstance;create.argtypes=[C.POINTER(GUID),C.POINTER(GUID),C.POINTER(C.c_void_p)];create.restype=HRESULT
    clsid=guid('73e22d93-e6ce-47f3-b5bf-f0664f39c1b0');iid=guid('228b4687-5a6a-4730-900c-9702b2203f54');compiler=C.c_void_p()
    status=create(C.byref(clsid),C.byref(iid),C.byref(compiler))
    if status<0:raise RuntimeError(status)
    folder=CAP/'Shaders';folder.mkdir(parents=True,exist_ok=True);rows=[]
    try:
        index=json.loads((CAP/'chunk_index.json').read_text(encoding='utf-8'))
        for record in index['records']:
            path=Path(record['path'])
            with path.open('rb') as f:head=f.read(36)
            if head[:4]!=b'DXBC':continue
            data=path.read_bytes()
            container_bytes,part_count=struct.unpack_from('<2I',data,24)
            if container_bytes!=len(data) or 32+part_count*4>len(data):raise ValueError(('DXBCbounds',record['chunk_id']))
            parts=[]
            for pi in range(part_count):
                offset=struct.unpack_from('<I',data,32+4*pi)[0];tag,size=struct.unpack_from('<4sI',data,offset)
                if offset+8+size>len(data):raise ValueError(('DXBCpartbounds',record['chunk_id'],pi))
                parts.append(tag.decode('ascii','replace'))
            target=folder/f"chunk_{record['chunk_id']:05d}.dxbc";target.write_bytes(data)
            root_signature=parse_root_signature(data) if parts==['RTS0'] else None
            if root_signature:assembly,error=None,None
            else:
                assembly,error=disassemble(data,compiler)
                if assembly is None and 'SHDR' in parts:assembly,error=disassemble_legacy(data)
            if assembly is not None:target.with_suffix('.asm.txt').write_text(assembly,encoding='utf-8')
            strings=[]
            if assembly:
                for word in ['skin','cloth','joint','bone','deform','morph','position']:
                    count=assembly.lower().count(word)
                    if count:strings.append({'word':word,'matches':count})
            row={'chunk_id':record['chunk_id'],'file':str(target),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                'parts':parts,'container_kind':'root_signature' if root_signature else 'shader',
                'root_signature':root_signature,'entry_name':re.search(r'EntryFunctionName: (\S+)',assembly).group(1) if assembly and re.search(r'EntryFunctionName: (\S+)',assembly) else None,
                'disassembly':str(target.with_suffix('.asm.txt')) if assembly else None,'disassembly_error':error,'keyword_matches':strings}
            rows.append(row)
    finally:method(compiler,2,C.c_ulong)(compiler)
    result={'capture':index['capture'],'dxbc_container_count':len(rows),'root_signature_count':sum(r['container_kind']=='root_signature' for r in rows),
      'shader_count':sum(r['container_kind']=='shader' for r in rows),'disassembled':sum(r['disassembly'] is not None for r in rows),
      'tool_dll':str(DLL),'rows':rows,'note':'Root signature containers may have RTS0 and no executable shader. Identifiers are container chunk IDs, not resource or draw IDs.'}
    (CAP/'shader_index.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'containers':len(rows),'disassembled':result['disassembled'],'errors':[(r['chunk_id'],r['disassembly_error']) for r in rows if r['disassembly_error']],'keyword_candidates':[(r['chunk_id'],r['keyword_matches']) for r in rows if any(w['word'] in ['skin','cloth','joint','bone','deform','morph'] for w in r['keyword_matches'])]},indent=2))

if __name__=='__main__':main()
