import sys, os, struct, types, math, json, traceback
from collections import namedtuple
from mathutils import Vector, Matrix, Quaternion

PLUGIN_DIR=r"D:/Unpack_3A/TLOU2/Tools/Noesis4474/plugins/python"
if PLUGIN_DIR not in sys.path: sys.path.insert(0,PLUGIN_DIR)
INPUT_NAME=''
OUTPUT_NAME=''

# --- minimal Noesis modules used by fmt_nd_pak.py ---
noesis=types.ModuleType('noesis')
noesis.NOEUSERVAL_FILEPATH=1
noesis.NMSHAREDFL_WANTGLOBALARRAY=1
noesis.RPGEODATA_FLOAT=0; noesis.RPGEODATA_HALFFLOAT=1; noesis.RPGEODATA_BYTE=2; noesis.RPGEODATA_UBYTE=3; noesis.RPGEODATA_USHORT=4; noesis.RPGEODATA_UINT=5
noesis.RPGEO_TRIANGLE=3
noesis.NOESISTEX_RGBA32=0
noesis.FOURCC_BC1=1; noesis.FOURCC_BC2=2; noesis.FOURCC_BC3=3; noesis.FOURCC_BC4=4; noesis.FOURCC_BC5=5; noesis.FOURCC_BC6=6; noesis.FOURCC_BC7=7
noesis.FOURCC_BC6S=6; noesis.FOURCC_DXT1=1
noesis.NMATFLAG_TWOSIDED=1; noesis.NMATFLAG_NORMALMAP_FLIPY=2; noesis.NMATFLAG_NORMALMAP_NODERZ=4
noesis.NMATFLAG_PBR_METAL=8; noesis.NMATFLAG_PBR_SPEC=16; noesis.NMATFLAG_PBR_SPEC_IR_RG=32
noesis.NOEC_ENCODEDXT_BC1=1; noesis.NOE_ENCODEDXT_BC1=1; noesis.NOE_ENCODEDXT_BC3=3; noesis.NOE_ENCODEDXT_BC4=4; noesis.NOE_ENCODEDXT_BC5=5; noesis.NOE_ENCODEDXT_BC6S=6; noesis.NOE_ENCODEDXT_BC7=7
noesis.OPTFLAG_WANTARG=1
noesis.NOEUSERVAL_FILEPATH=1
def _false(*a,**k): return False
noesis.optWasInvoked=_false; noesis.optGetArg=lambda *a: None; noesis.logPopup=lambda *a: None; noesis.getPluginsPath=lambda: PLUGIN_DIR+'/'
noesis.getInputName=lambda: INPUT_NAME; noesis.getOutputName=lambda: OUTPUT_NAME; noesis.userPrompt=lambda *a: None; noesis.getAPIVersion=lambda: 1
noesis.register=lambda *a: 1; noesis.addOption=lambda *a: None; noesis.setHandlerTypeCheck=lambda *a:None; noesis.setHandlerLoadModel=lambda *a:None; noesis.setHandlerWriteModel=lambda *a:None; noesis.setTypeSharedModelFlags=lambda *a:None
noesis.logOutput=lambda *a:None; noesis.logError=lambda *a:None; noesis.isPreviewModuleRAPIValid=lambda:False
sys.modules['noesis']=noesis
noewin=types.ModuleType('noewin'); sys.modules['noewin']=noewin

class NoeBitStream:
    def __init__(self,data=None): self.buf=bytearray(data or b''); self.pos=0; self.bitbuf=0; self.bitcount=0
    def tell(self): return self.pos
    def seek(self,p,whence=0): self.pos=(p if whence==0 else self.pos+p if whence==1 else len(self.buf)+p); self.bitbuf=0; self.bitcount=0
    def getSize(self): return len(self.buf)
    def checkEOF(self): return self.pos>=len(self.buf)
    def getBuffer(self): return bytes(self.buf)
    def readBytes(self,n):
        n=int(n)
        # Native Noesis byte reads align after a bit-field read.
        if self.bitcount: self.bitcount=0; self.bitbuf=0
        out=bytes(self.buf[self.pos:self.pos+n]); self.pos+=n
        if len(out)<n: out += b'\0'*(n-len(out))
        return out
    def readByte(self): return struct.unpack('<b',self.readBytes(1))[0]
    def readUByte(self): return self.readBytes(1)[0]
    def readUShort(self): return struct.unpack('<H',self.readBytes(2))[0]
    def readShort(self): return struct.unpack('<h',self.readBytes(2))[0]
    def readUInt(self):
        b=self.readBytes(4)
        if len(b)!=4: b=(b+b'\0'*4)[:4]
        return struct.unpack('<I',b)[0]
    def readInt(self): return struct.unpack('<i',self.readBytes(4))[0]
    def readUInt64(self): return struct.unpack('<Q',self.readBytes(8))[0]
    def readInt64(self): return struct.unpack('<q',self.readBytes(8))[0]
    def readFloat(self): return struct.unpack('<f',self.readBytes(4))[0]
    def readString(self):
        st=self.pos
        while self.pos<len(self.buf) and self.buf[self.pos]!=0:self.pos+=1
        out=bytes(self.buf[st:self.pos]).decode('utf-8','ignore'); self.pos+=1; return out
    def readBits(self,n):
        v=0; shift=0
        while shift<n:
            if self.bitcount==0:
                self.bitbuf=self.buf[self.pos] if self.pos < len(self.buf) else 0
                self.pos += 1; self.bitcount=8
            take=min(self.bitcount,n-shift)
            v |= (self.bitbuf & ((1<<take)-1)) << shift
            self.bitbuf >>= take; self.bitcount-=take; shift+=take
        return v
    def writeBytes(self,b): self.buf.extend(b)
    def writeByte(self,b): self.buf.append(b&255)
    def writeUInt(self,v): self.buf.extend(struct.pack('<I',v))
    def writeUInt64(self,v): self.buf.extend(struct.pack('<Q',v))
    def writeUShort(self,v): self.buf.extend(struct.pack('<H',v))
    def writeInt(self,v): self.buf.extend(struct.pack('<i',v))
    def writeFloat(self,v): self.buf.extend(struct.pack('<f',v))
    def writeString(self,s): self.buf.extend(s.encode()+b'\0')

def _vec3(v=(0,0,0)): return Vector((float(v[0]),float(v[1]),float(v[2])))
class NoeVec3(Vector):
    def __new__(cls,v=(0,0,0)): return Vector.__new__(cls,(float(v[0]),float(v[1]),float(v[2])))
class NoeVec4(Vector):
    def __new__(cls,v=(0,0,0,0)): return Vector.__new__(cls,(float(v[0]),float(v[1]),float(v[2]),float(v[3])))
    def toVec3(self): return NoeVec3(self[:3])
class NoeQuat:
    def __init__(self,v=(0,0,0,1)): self.q=Quaternion((float(v[3]),float(v[0]),float(v[1]),float(v[2])))
    def transpose(self): return self
    def toMat43(self): return NoeMat43.from_matrix(self.q.to_matrix().to_4x4())
    def toBytes(self): return struct.pack('<4f',self.q.x,self.q.y,self.q.z,self.q.w)
class NoeMat43:
    def __init__(self,rows=None):
        self.m=Matrix.Identity(4) if rows is None else Matrix([[float(x) for x in row]+[0]*(4-len(row)) for row in rows])
        if len(self.m)<4:self.m=Matrix.Identity(4)
    @classmethod
    def from_matrix(cls,m): o=cls(); o.m=m.copy(); return o
    def __getitem__(self,i): return NoeVec3((self.m[i][0],self.m[i][1],self.m[i][2])) if i<3 else NoeVec3((self.m[3][0],self.m[3][1],self.m[3][2]))
    def __setitem__(self,i,v):
        if i<3:
            for j in range(3): self.m[i][j]=float(v[j])
        else:
            for j in range(3): self.m[3][j]=float(v[j])
    def __mul__(self,o):
        if isinstance(o,NoeMat43): return NoeMat43.from_matrix(self.m@o.m)
        return self
    def inverse(self): return NoeMat43.from_matrix(self.m.inverted())
    def toQuat(self): return NoeQuat((0,0,0,1))
    def toBytes(self): return struct.pack('<12f',*(self.m[i][j] for i in range(3) for j in range(4)))
class NoeMat44:
    def __init__(self,rows): self.m=Matrix([[float(x) for x in r] for r in rows])
    def toMat43(self): return NoeMat43.from_matrix(self.m)
class NoeBone:
    def __init__(self,index,name,mat,parentName=None,parentIndex=-1): self.index=index; self.name=name; self.mat=mat; self.parentName=parentName; self.parentIndex=parentIndex
    def getMatrix(self): return self.mat
class NoeUserStream:
    def __init__(self,name,data,stride,ofs): self.name=name; self.data=data; self.stride=stride; self.ofs=ofs
class NoeVertWeight:
    def __init__(self,ids,weights): self.ids=ids; self.weights=weights
class NoeMaterial:
    def __init__(self,name,*args): self.name=name; self.flags=0
    def __getattr__(self,n): return lambda *a,**k: None
class NoeModel: 
    def __init__(self,*a,**k): self.meshes=[]
class NoeModelMaterials:
    def __init__(self,*a,**k): pass
class NoeTexture:
    def __init__(self,*a,**k): pass

inc=types.ModuleType('inc_noesis')
for name,obj in list(globals().items()):
    if name.startswith('Noe') or name in ['NoeBitStream']:
        setattr(inc,name,obj)
inc.NoeVec3=NoeVec3; inc.NoeVec4=NoeVec4; inc.NoeQuat=NoeQuat; inc.NoeMat43=NoeMat43; inc.NoeMat44=NoeMat44; inc.NoeBone=NoeBone; inc.NoeUserStream=NoeUserStream; inc.NoeBitStream=NoeBitStream; inc.NoeVertWeight=NoeVertWeight
inc.noesis=noesis; inc.rapi=None; inc.struct=struct
# math/utility globals used by plugin
inc.NoeModelMaterials=NoeModelMaterials; inc.NoeTexture=NoeTexture; inc.NoeMaterial=NoeMaterial; inc.NoeModel=NoeModel
sys.modules['inc_noesis']=inc

# rapi capture implementation
class Capture:
    def __init__(self): self.meshes=[]; self.current={}; self.name='mesh'; self.material=None; self.expected_vertex_count=0
    def reset(self): self.current={}; self.expected_vertex_count=0
cap=Capture()
rapi=types.ModuleType('rapi')
rapi.getInputName=lambda: INPUT_NAME; rapi.getOutputName=lambda: OUTPUT_NAME; rapi.getLocalFileName=lambda p: os.path.basename(p); rapi.getExtensionlessName=lambda p: os.path.splitext(os.path.basename(p))[0]
rapi.checkFileExists=os.path.exists; rapi.loadIntoByteArray=lambda p: open(p,'rb').read()
rapi.rpgCreateContext=lambda: cap
rapi.rpgSetName=lambda n: setattr(cap,'name',n)
rapi.rpgSetTransform=lambda *a: None; rapi.rpgSetLightmap=lambda *a: None
rapi.rpgSetMaterial=lambda n: setattr(cap,'material',n)
rapi.rpgBindPositionBuffer=lambda b,t,s: cap.current.update(pos=(bytes(b),t,s))
rapi.rpgBindPositionBufferOfs=lambda b,t,s,o: cap.current.update(pos=(bytes(b)[o:],t,s))
rapi.rpgBindNormalBuffer=lambda b,t,s: cap.current.update(nrm=(bytes(b),t,s))
rapi.rpgBindNormalBufferOfs=lambda b,t,s,o: cap.current.update(nrm=(bytes(b)[o:],t,s))
rapi.rpgBindTangentBuffer=lambda b,t,s: cap.current.update(tan=(bytes(b),t,s))
rapi.rpgBindTangentBufferOfs=lambda b,t,s,o: cap.current.update(tan=(bytes(b)[o:],t,s))
rapi.rpgBindUV1Buffer=lambda b,t,s: cap.current.update(uv0=(bytes(b),t,s))
rapi.rpgBindUV2Buffer=lambda b,t,s: cap.current.update(uv1=(bytes(b),t,s))
rapi.rpgBindUVXBuffer=lambda b,t,s,idx,count: cap.current.update(**{f'uv{idx}':(bytes(b),t,s)})
rapi.rpgBindUV1BufferOfs=lambda b,t,s,o: cap.current.update(uv0=(bytes(b)[o:],t,s))
rapi.rpgBindUV2BufferOfs=lambda b,t,s,o: cap.current.update(uv1=(bytes(b)[o:],t,s))
rapi.rpgBindUVXBufferOfs=lambda b,t,s,idx,count,o: cap.current.update(**{f'uv{idx}':(bytes(b)[o:],t,s)})
rapi.rpgBindColorBuffer=lambda *a,**k: None; rapi.rpgBindColorBufferOfs=lambda *a,**k: None
rapi.rpgBindBoneIndexBuffer=lambda b,t,s,n: cap.current.update(bidx=(bytes(b),t,s,n))
rapi.rpgBindBoneIndexBufferOfs=lambda b,t,s,o,n: cap.current.update(bidx=(bytes(b)[o:],t,s,n))
rapi.rpgBindBoneWeightBuffer=lambda b,t,s,n: cap.current.update(bwgt=(bytes(b),t,s,n))
rapi.rpgBindBoneWeightBufferOfs=lambda b,t,s,o,n: cap.current.update(bwgt=(bytes(b)[o:],t,s,n))
def _capture_commit(b,t,count,prim,plot):
    pb=cap.current.get('pos',(b'',0,1)); raw=pb[0]; typ=pb[1]; stride=pb[2]
    # Compressed TLOU2 positions are four-float records; Noesis binds them as a
    # 12-byte XYZ stream while silently ignoring the fourth component.
    vc=int(cap.expected_vertex_count or ((len(raw)//16) if (typ==noesis.RPGEODATA_FLOAT and len(raw)%16==0) else (len(raw)//max(1,stride))))
    cap.meshes.append({'name':cap.name,'material':cap.material,'binds':dict(cap.current),'indices':bytes(b),'index_type':t,'count':count,'vertex_count':vc})
rapi.rpgCommitTriangles=_capture_commit
rapi.rpgClearBufferBinds=lambda: cap.reset()
rapi.rpgConstructModelAndSort=lambda: NoeModel()
rapi.rpgConstructModel=lambda: NoeModel(); rapi.rpgConstructModelSlim=lambda: NoeModel(); rapi.rpgSetOption=lambda *a:None
rapi.multiplyBones=lambda x:x
rapi.callExtensionMethod=lambda *a: None; rapi.setPreviewOption=lambda *a: None
rapi.imageDecodeRaw=lambda *a: b''; rapi.imageDecodeDXT=lambda *a: b''; rapi.imageResample=lambda *a: b''
rapi.getInputName=lambda: INPUT_NAME; rapi.getOutputName=lambda: OUTPUT_NAME
sys.modules['rapi']=rapi
inc.rapi=rapi
ns_cap_placeholder = None

# load plugin source without registration execution
ns={'__name__':'ndplugin', 'cap':cap}
code=open(os.path.join(PLUGIN_DIR,'fmt_nd_pak.py'),encoding='utf-8-sig').read()
# Guard malformed/corrupt descriptor counts while using the plugin parser outside Noesis.
# Real Noesis aborts an invalid stream; the compatibility capture should skip that submesh
# and keep every valid mesh preceding it.
code=code.replace('for i, sm in enumerate(self.submeshes):', 'for i, sm in enumerate(self.submeshes):\n\t\t\t\tif sm.numVerts > 200000 or sm.numIndices > 600000:\n\t\t\t\t\tprint("Skipping suspicious submesh", i, sm.name, sm.numVerts, sm.numIndices)\n\t\t\t\t\tcontinue')
code=code.replace('for v in range(sd.numVerts):', 'for v in range(min(sd.numVerts, sm.numVerts, 200000)):')
code=code.replace('rapi.rpgBindPositionBuffer(firstPosBuff,', 'cap.expected_vertex_count = sm.numVerts\n\t\t\t\t\trapi.rpgBindPositionBuffer(firstPosBuff,')
# TLOU2 PC geometry descriptors carry an 8-byte field before the counts and
# another 8-byte field at the end of the 192-byte descriptor.
code=code.replace('uknStringOffs = bs.readUInt64()\n\t\t\t\t\tm_numVertexes = bs.readUInt()', 'uknStringOffs = bs.readUInt64()\n\t\t\t\t\tuknPC0 = bs.readUInt64()\n\t\t\t\t\tm_numVertexes = bs.readUInt64() if False else bs.readUInt()')
code=code.replace('ukn32_5 = bs.readUInt()\n\t\t\t\telse:', 'ukn32_5 = bs.readUInt()\n\t\t\t\t\tuknPC1 = bs.readUInt64()\n\t\t\t\telse:', 1)
code=code.replace('self.submeshes[i].offset = SubmeshesOffs + 176*i', 'self.submeshes[i].offset = SubmeshesOffs + (192 if (dialogOptions.isTLOU2 or dialogOptions.isTLOUP1) else 176)*i')
code=code.replace('self.entriesList = []', 'self.entriesList = []\n\t\tself.entryAbs = []')
code=code.replace('self.entriesList.append(PakEntry(type=m_itemType, offset = m_resItemOffset))', 'self.entriesList.append(PakEntry(type=m_itemType, offset = m_resItemOffset))\n\t\tself.entryAbs.append(start + m_resItemOffset)')
exec(compile(code,os.path.join(PLUGIN_DIR,'fmt_nd_pak.py'),'exec'),ns)
# force globals/options
ns['gameName']='TLOU2'; ns['dialogOptions'].doLoadTex=False; ns['dialogOptions'].doConvertTex=False; ns['dialogOptions'].doLODs=False; ns['dialogOptions'].doLoadBase=False; ns['dialogOptions'].isTLOU2=True
ns['BaseDirectories']['TLOU2']=r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/'
PakFile=ns['PakFile']; NoeBitStream=ns['NoeBitStream']

root=r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97'
packages=['anim-ellie-player-movement.pak']
outroot=r'D:/TLOU2_UE5_8_Codex/Exports/ExactDebug'; os.makedirs(outroot,exist_ok=True)
results=[]; skel=None

def _matrix_rows(mat):
    try:
        return [[float(mat.m[i][j]) for j in range(4)] for i in range(4)]
    except Exception:
        try: return [[float(mat[i][j]) for j in range(4)] for i in range(4)]
        except Exception: return None

def export_capture(pak, label):
    """Persist parser capture in a compact, tool-agnostic form for Blender/UE import."""
    try:
        import numpy as np
    except Exception as e:
        print('numpy unavailable:', e); return
    folder=os.path.join(outroot, label); os.makedirs(folder, exist_ok=True)
    bones=[]
    for b in (pak.boneList or []):
        bones.append({'index':int(getattr(b,'index',len(bones))), 'name':str(getattr(b,'name','bone_%04d'%len(bones))),
                      'parentIndex':int(getattr(b,'parentIndex',-1)), 'parentName':getattr(b,'parentName',None),
                      'matrix':_matrix_rows(getattr(b,'mat',None))})
    meshes=[]
    for mi,m in enumerate(cap.meshes):
        stem='mesh_%04d'%mi; npz_name=stem+'.npz'
        arrays={'indices_raw':np.frombuffer(m.get('indices',b''),dtype=np.uint8)}
        bind_meta={}
        for key,val in (m.get('binds') or {}).items():
            raw,typ,stride,*rest=val
            arrays[key+'_raw']=np.frombuffer(raw,dtype=np.uint8)
            bind_meta[key]={'type':int(typ),'stride':int(stride),'extra':[int(x) for x in rest]}
        np.savez_compressed(os.path.join(folder,npz_name), **arrays)
        meshes.append({'name':str(m.get('name','mesh_%04d'%mi)), 'material':str(m.get('material') or ''),
                       'count':int(m.get('count',0)), 'vertex_count':int(m.get('vertex_count',0)),
                       'index_type':int(m.get('index_type',0)), 'npz':npz_name, 'bindings':bind_meta})
    meta={'source':label,'boneCount':len(bones),'bones':bones,'meshCount':len(meshes),'meshes':meshes,
          'parser':'fmt_nd_pak.py via Blender compatibility rapi capture','pak':os.path.basename(INPUT_NAME)}
    with open(os.path.join(folder,'capture.json'),'w',encoding='utf-8') as f: json.dump(meta,f,indent=2)
    print('Wrote capture', folder, len(bones), 'bones', len(meshes), 'meshes')

def export_texture_headers(pak, label):
    """Write VRAM descriptor metadata; payloads are resolved from texturedict3 later."""
    out=[]; bs=pak.bs; last_page=(pak.pakPageEntries[-1] if getattr(pak,'pakPageEntries',None) else (0,0))
    for h, tup in (getattr(pak,'vrams',{}) or {}).items():
        off=int(tup[0]); name=str(tup[1]);
        try:
            bs.seek(off+40); pakOffset=bs.readUInt(); bs.readUInt(); size=bs.readUInt(); texDict=bs.readUInt(); hh=bs.readUInt64(); bs.readUInt(); typ=bs.readUInt(); fmt=bs.readUInt(); bs.readUInt(); mips=bs.readUInt(); w=bs.readUInt(); he=bs.readUInt()
            out.append({'hash':int(h),'name':name,'descriptor_offset':off,'payload_offset':int(pakOffset),'payload_abs':int(pakOffset+last_page[0]+last_page[1]),'size':int(size),'dict_id':int(texDict),'format':int(fmt),'mips':int(mips),'width':int(w),'height':int(he),'source_pak':os.path.basename(INPUT_NAME)})
        except Exception as e: out.append({'hash':int(h),'name':name,'descriptor_offset':off,'error':repr(e)})
    with open(os.path.join(outroot,label,'texture_headers.json'),'w',encoding='utf-8') as f: json.dump(out,f,indent=2)

for fname in packages:
    path=os.path.join(root,fname)
    INPUT_NAME=path; OUTPUT_NAME=os.path.join(outroot,fname+'.json')
    ns['INPUT_NAME']=INPUT_NAME; ns['OUTPUT_NAME']=OUTPUT_NAME
    cap.meshes=[]; cap.current={}
    try:
        pak=PakFile(NoeBitStream(open(path,'rb').read()), {'path':path})
        pak.readPakHeader(); pak.readPak()
        print('ANIM_PAK',fname,'entries',[(getattr(x,'type',None),getattr(x,'offset',None)) for x in getattr(pak,'entriesList',[])[:100]],'geo',pak.geoOffset,'joint',pak.jointOffset,'pages',len(pak.pakPageEntries),'page_entries',pak.pakPageEntries,'pointer_count',len(pak.pointerPageIds))
        if 'anim-' in fname:
            for ei,e in enumerate(getattr(pak,'entriesList',[])):
                if getattr(e,'type',None) in ('ANIM_RAWCHANNELS','ANIM','ANIM_GROUP'):
                    rel=int(getattr(e,'offset',0)); off=int(getattr(pak,'entryAbs',[])[ei] if getattr(pak,'entryAbs',None) else pak.pakPageEntries[0][0]+rel); raw=bytes(pak.bs.buf[off:off+256]); print('ANIM_HEX',fname,ei,getattr(e,'type',None),rel,off,raw.hex())
                    try:
                        pak.bs.seek(off+48)
                        vals=[pak.bs.readUInt(),pak.bs.readUInt()]
                        for _ in range(5): vals.append(pak.readPointerFixup())
                        print('ANIM_FIELDS',fname,ei,getattr(e,'type',None),vals)
                    except Exception as ex: print('ANIM_FIELDS_ERR',repr(ex))
        if fname=='ellie-skel.pak': skel=pak
        else:
            if skel: pak.boneList=skel.boneList; pak.boneMap=skel.boneMap; pak.boneDict=skel.boneDict
            if fname == 'ellie16-patrol-body.pak':
                dbgbs=pak.bs; dbgbase=pak.geoOffset[0]+pak.geoOffset[1]+ns.get('ResItemPaddingSz',48); dbgbs.seek(dbgbase)
                dbghead=[dbgbs.readUInt() for _ in range(10)]; dbgptr=pak.readPointerFixup()
                print('GEO_DEBUG', dbgbase, dbghead, 'SubmeshesOffs', dbgptr)
                raw=bytes(dbgbs.buf[dbgptr:dbgptr+256]) if dbgptr is not None and dbgptr>=0 else b''
                print('DESC_HEAD', raw.hex())
                if raw:
                    for off in [120,128,132,136,140,144,148,152,156,160,164,168,172,176,180,184,188]:
                        print('DESC_U32', off, struct.unpack_from('<I',raw,off)[0])
                    for off in [32,40,48,56,64,72,80,88,96,104,112,120]:
                        print('DESC_U64', off, struct.unpack_from('<Q',raw,off)[0])
                    for baseoff in [176,192,200]:
                        print('DESC2', baseoff, struct.unpack_from('<8I',raw,baseoff) if len(raw)>=baseoff+32 else 'short')
            pak.loadGeometry()
            print('SUBMESH_COUNTS', [(sm.name, int(sm.numVerts), int(sm.numIndices)) for sm in (pak.submeshes or [])[:30]])
            print('STREAM0', [(int(sd.type), int(sd.stride), int(sd.numVerts), list(sd.sizes), list(sd.qScale), list(sd.qOffs), int(sd.offset)) for sd in (pak.submeshes[0].streamDescs or [])])
            print('CAPTURE_BINDINGS', [(m.get('name'), m.get('count'), m.get('vertex_count'), {k:(len(v[0]),v[1],v[2]) for k,v in m.get('binds',{}).items()}) for m in cap.meshes])
            export_capture(pak, os.path.splitext(fname)[0].replace('-','_'))
            export_texture_headers(pak, os.path.splitext(fname)[0].replace('-','_'))
        results.append({'file':fname,'bones':len(pak.boneList or []),'submeshes':len(pak.submeshes or []),'captured_meshes':len(cap.meshes),'geo':pak.geoOffset,'joint':pak.jointOffset})
    except Exception as e:
        traceback.print_exc(); results.append({'file':fname,'error':repr(e)})
open(os.path.join(outroot,'parse_results.json'),'w').write(json.dumps(results,indent=2,default=str))
print(json.dumps(results,indent=2,default=str))









