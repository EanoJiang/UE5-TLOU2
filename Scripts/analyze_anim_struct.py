import struct, os, json, math, sys

def cstr(b,o):
    if o<0 or o>=len(b): return ''
    e=b.find(b'\0',o); return b[o:e if e>=0 else len(b)].decode('utf-8','replace')
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def f32(b,o): return struct.unpack_from('<f',b,o)[0]
def f16(b,o): return struct.unpack_from('<e',b,o)[0]
def hexes(b,o,n): return b[o:o+n].hex(' ')
def describe(b,o,n=128):
    print(f'OFFSET {o} HEX {hexes(b,o,n)}')
    print('U32:', [hex(u32(b,o+i)) for i in range(0,min(n,64),4)])
    print('U64:', [hex(u64(b,o+i)) for i in range(0,min(n,64),8)])
    print('F32:', [round(f32(b,o+i),7) for i in range(0,min(n,64),4)])
    print('F16:', [round(f16(b,o+i),6) for i in range(0,min(n,64),2)])

path=sys.argv[1] if len(sys.argv)>1 else r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak'
b=open(path,'rb').read()
magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',b,0)
pages=[struct.unpack_from('<3I',b,pt+p*12) for p in range(pct)]
print('FILE',path,'size',len(b),'pages',pages)
for pi,(po,ps,_) in enumerate(pages):
    n=u16(b,po+18); print('PAGE',pi,'offset',po,'size',ps,'entries',n)
    for j in range(n):
        q=po+20+j*16; no,ro=struct.unpack_from('<QI',b,q); rs=po+ro
        if j<2: print('RAW_ENTRY_WORDS',j,'q',q,'no',no,'ro',ro,'rs',rs,'bytes',b[q:q+24].hex())
        print('RS_WORDS',j,hex(u64(b,rs)),hex(u64(b,rs+8)), 'names', repr(cstr(b,po+u64(b,rs))), repr(cstr(b,po+u64(b,rs+8))))
        try: name=cstr(b,po+u64(b,rs)); typ=cstr(b,po+u64(b,rs+8))
        except: continue
        print('ENTRY_RAW',j,repr(name),repr(typ),'rs',rs,'rel',ro)
        if typ not in ('ANIM_RAWCHANNELS','ANIM','ANIM_GROUP'): continue
        print('ENTRY',j,name,typ,'rs',rs,'rel',ro); describe(b,rs,160)
        if typ in ('ANIM','ANIM_GROUP'):
            for off in range(48,160,8):
                v=u64(b,rs+off)
                if 0<v<ps and po+v<len(b):
                    print('ANIM_PTR',typ,name,'field',off,'rel',hex(v),'abs',po+v); describe(b,po+v,96)
        if typ!='ANIM_RAWCHANNELS': continue
        base=rs+48; count=u32(b,base); print('RAWCOUNT',count)
        seen=[]
        for off in range(0,min(512,ps-(base-po)-8),8):
            v=u64(b,base+off)
            if 0<v<ps and v not in seen and po+v+4<len(b):
                seen.append(v); print('BLOCK from',off,hex(v),'abs',po+v); describe(b,po+v,96)
