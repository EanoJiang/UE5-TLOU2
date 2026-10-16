import bpy, os, json, struct, zlib, binascii, sys

# BC7 is decoded with the small, MIT-licensed texture2ddecoder extension.
# Keep a vendored copy beside this script so the extraction is reproducible
# with the bundled Blender Python; a system install is used as a fallback.
VENDOR=os.path.join(os.path.dirname(__file__),'vendor')
if os.path.isdir(VENDOR) and VENDOR not in sys.path: sys.path.insert(0,VENDOR)
try:
    import texture2ddecoder
except Exception:
    texture2ddecoder=None

ROOT=r'D:/TLOU2_UE5_8_Codex'
HDRROOT=os.path.join(ROOT,'Exports','ExactDebug')
SRCROOT=r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97'
OUT=os.path.join(ROOT,'Exports','TexturesDecoded'); os.makedirs(OUT,exist_ok=True)
folders=['ellie16_patrol_body','ellie_patrol_jacket','ellie_patrol_hoodie_cloth','ellie_patrol_pants','ellie_patrol_boots','ellie_patrol_hair','backpack_ellie','ellie_head','ellie_patrol_l_glove','ellie_patrol_r_glove']

FMT={0x47:'BC1',0x48:'BC1',0x4A:'BC2',0x4D:'BC3',0x4E:'BC3',0x50:'BC4',0x53:'BC5',0x62:'BC7',0x63:'BC7',0x1C:'RGBA8',0x1D:'RGBA8',0x31:'RG8',0x3D:'R8',0x57:'BGRA8',0x5B:'BGRA8'}

def rgb565(v):
    r=((v>>11)&31)*255//31; g=((v>>5)&63)*255//63; b=(v&31)*255//31
    return r,g,b
def bc4(block):
    a0,a1=block[0],block[1]; vals=[a0,a1]
    if a0>a1: vals += [(6*a0+a1)//7,(5*a0+2*a1)//7,(4*a0+3*a1)//7,(3*a0+4*a1)//7,(2*a0+5*a1)//7,(a0+6*a1)//7]
    else: vals += [(4*a0+a1)//5,(3*a0+2*a1)//5,(2*a0+3*a1)//5,(a0+4*a1)//5,0,255]
    bits=int.from_bytes(block[2:8],'little'); return [vals[(bits>>(3*i))&7] for i in range(16)]
def bc1(block):
    c0,c1=struct.unpack_from('<HH',block,0); p=[(*rgb565(c0),255),(*rgb565(c1),255)]
    if c0>c1: p += [tuple((2*p[0][k]+p[1][k])//3 for k in range(3))+(255,),tuple((p[0][k]+2*p[1][k])//3 for k in range(3))+(255,)]
    else: p += [tuple((p[0][k]+p[1][k])//2 for k in range(3))+(255,),(0,0,0,0)]
    bits=struct.unpack_from('<I',block,4)[0]; return [p[(bits>>(2*i))&3] for i in range(16)]
def decode(data,w,h,fmt):
    if fmt in ('BC1','BC2','BC3','BC4','BC5'):
        bs=8 if fmt in ('BC1','BC4') else 16; bw=(w+3)//4; bh=(h+3)//4; out=bytearray(w*h*4)
        for by in range(bh):
            for bx in range(bw):
                off=(by*bw+bx)*bs; block=data[off:off+bs]
                if len(block)<bs: block=block+b'\0'*(bs-len(block))
                if fmt=='BC1': pix=bc1(block)
                elif fmt=='BC4': g=bc4(block); pix=[(x,x,x,255) for x in g]
                elif fmt=='BC3':
                    a=bc4(block[:8]); c=bc1(block[8:]); pix=[(c[i][0],c[i][1],c[i][2],a[i]) for i in range(16)]
                elif fmt=='BC5':
                    r=bc4(block[:8]); g=bc4(block[8:]); pix=[(r[i],g[i],255,255) for i in range(16)]
                else:
                    # BC2 explicit alpha + BC1 color
                    c=bc1(block[8:]); ab=int.from_bytes(block[:8],'little'); pix=[]
                    for i in range(16): pix.append((c[i][0],c[i][1],c[i][2],((ab>>(4*i))&15)*17))
                for iy in range(4):
                    y=by*4+iy
                    if y>=h: continue
                    for ix in range(4):
                        x=bx*4+ix
                        if x>=w: continue
                        p=pix[iy*4+ix]; j=(y*w+x)*4; out[j:j+4]=bytes(p)
        return bytes(out)
    if fmt=='BC7':
        if texture2ddecoder is None:
            return None
        # ND stores a complete top mip at the descriptor payload address;
        # lower mips follow it and are intentionally ignored for the PNG
        # preview.  BC7 is 16 bytes per 4x4 block.
        top=((w+3)//4)*((h+3)//4)*16
        if len(data)<top:
            return None
        return texture2ddecoder.decode_bc7(data[:top],w,h)
    bpp={'R8':1,'RG8':2,'RGBA8':4,'BGRA8':4}.get(fmt)
    if bpp:
        raw=data[:w*h*bpp]; out=bytearray(w*h*4)
        for i in range(w*h):
            q=raw[i*bpp:(i+1)*bpp]
            if fmt=='R8': p=(q[0],q[0],q[0],255) if q else (0,0,0,255)
            elif fmt=='RG8': p=(q[0],q[1],255,255) if len(q)>=2 else (0,0,0,255)
            elif fmt=='BGRA8': p=(q[2],q[1],q[0],q[3]) if len(q)>=4 else (0,0,0,255)
            else: p=tuple(q)+(255,) if len(q)==3 else tuple(q)+(0,)*(4-len(q))
            out[i*4:i*4+4]=bytes(p)
        return bytes(out)
    return None
def png(path,w,h,rgba):
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',binascii.crc32(t+d)&0xffffffff)
    scan=b''.join(b'\0'+rgba[y*w*4:(y+1)*w*4] for y in range(h))
    blob=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(scan,6))+chunk(b'IEND',b'')
    open(path,'wb').write(blob)

records=[]; seen=set()
for folder in folders:
    hp=os.path.join(HDRROOT,folder,'texture_headers.json')
    if not os.path.exists(hp): continue
    for h in json.load(open(hp,encoding='utf-8')):
        if h.get('hash') in seen: continue
        seen.add(h.get('hash')); rec=dict(h); rec['folder']=folder; fmt=FMT.get(int(h.get('format',0))); rec['format_name']=fmt
        src=os.path.join(SRCROOT,h.get('source_pak',''))
        try:
            with open(src,'rb') as f: f.seek(int(h['payload_abs'])); raw=f.read(int(h['size']))
            rec['payload_bytes']=len(raw)
            rgba=decode(raw,int(h['width']),int(h['height']),fmt) if fmt else None
            if rgba:
                outname=os.path.splitext(os.path.basename(h['name']))[0]+'.png'; outpath=os.path.join(OUT,outname); png(outpath,int(h['width']),int(h['height']),rgba); rec['decoded_path']=outpath; rec['decoded']=True
            else: rec['decoded']=False; rec['reason']='BC7/unsupported or tiled payload'
        except Exception as e: rec['decoded']=False; rec['error']=repr(e)
        records.append(rec)
json.dump(records,open(os.path.join(OUT,'texture_decode_manifest.json'),'w',encoding='utf-8'),indent=2)
print('TEXTURE_DECODED',sum(1 for r in records if r.get('decoded')), '/',len(records))
