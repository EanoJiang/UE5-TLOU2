"""Read original captured D3D12 buffer ranges by stable object UID.

Container chunks were independently decompressed by extract_ngfx_capture_chunks.
The metadata references an initial object index (chunk47211 in this capture).
Resource-state blobs reference 80-byte D3D12_BOX/data-page records. This reader
accepts the strictly checked one-dimensional buffer records only, and does not
guess how texture layouts are packed.
"""
from functools import lru_cache
import json
from pathlib import Path
import struct

ROOT=Path(r'D:/TLOU2_UE5_8_Codex/Exports/CaptureBuffers')
CHUNKS=ROOT/'Chunks'


@lru_cache(maxsize=8)
def read_chunk(chunk_id):
    return (CHUNKS/f'chunk_{chunk_id:05d}.bin').read_bytes()


@lru_cache(maxsize=1)
def object_index():
    b=read_chunk(47211)
    if len(b)%72: raise ValueError('initial object record stride')
    out={}
    for pos in range(0,len(b),72):
        uid,flags,api,function,cc,co,cs,sc,so,ss=struct.unpack_from('<QQII6Q',b,pos)
        if uid in out:raise ValueError('duplicate initial UID')
        out[uid]=dict(uid=uid,flags=flags,api=api,function_id=function,create_chunk=cc,
            create_offset=co,create_size=cs,state_chunk=sc,state_offset=so,state_size=ss)
    return out


def object_blob(uid,kind='state'):
    row=object_index()[uid]
    b=read_chunk(row[kind+'_chunk']);start=row[kind+'_offset'];size=row[kind+'_size']
    if not 0<=start<=start+size<=len(b):raise ValueError('object blob bounds')
    return b[start:start+size]


def _page(blob,pos):
    if pos+80>len(blob):return None
    left,top,front,right,bottom,back=struct.unpack_from('<6I',blob,pos)
    pitch,resource_offset,chunk,chunk_offset,reserved=struct.unpack_from('<5Q',blob,pos+24)
    subresource=struct.unpack_from('<I',blob,pos+64)[0]
    size=struct.unpack_from('<Q',blob,pos+68)[0]
    tail=struct.unpack_from('<I',blob,pos+76)[0]
    # The word at+76 belongs to the next record prefix or the following
    # serialized pointer tag (0xfa000002 after the final data-page record).
    # It is deliberately not treated as a zero field of the current page.
    if not (top==front==0 and bottom==back==1 and right>left and
            pitch==size==right-left and resource_offset==left and reserved==subresource==0):return None
    path=CHUNKS/f'chunk_{chunk:05d}.bin'
    if not path.exists() or chunk_offset+size>path.stat().st_size:return None
    return dict(resource_offset=resource_offset,bytes=size,chunk_id=chunk,
                chunk_offset=chunk_offset,state_record_offset=pos)


@lru_cache(maxsize=256)
def resource_pages(uid):
    blob=object_blob(uid)
    candidates=[]
    for start in range(min(128,len(blob))):
        first=_page(blob,start)
        if first is None or first['resource_offset']!=0:continue
        pages=[];pos=start;end=0
        while True:
            p=_page(blob,pos)
            if p is None or p['resource_offset']!=end:break
            pages.append(p);end+=p['bytes'];pos+=80
        candidates.append((end,pages))
    if not candidates:raise ValueError(f'UID{uid}: no strictly validated contiguous buffer page table')
    candidates.sort(key=lambda r:r[0],reverse=True)
    if len(candidates)>1 and candidates[0][0]==candidates[1][0]:raise ValueError(f'UID{uid}: ambiguous buffer page table')
    return candidates[0][1]


def read_resource(uid,offset,size):
    """Return a captured initial-state buffer range, with bounds validation.

    CPU writes later in the captured frame may supersede these initial bytes;
    those mutable updates require separate event/state reconstruction.
    """
    pages=resource_pages(uid);end=pages[-1]['resource_offset']+pages[-1]['bytes']
    if not 0<=offset<=offset+size<=end:raise ValueError((uid,offset,size,end))
    out=bytearray();target_end=offset+size
    for p in pages:
        start=max(offset,p['resource_offset']);stop=min(target_end,p['resource_offset']+p['bytes'])
        if stop<=start:continue
        local=p['chunk_offset']+start-p['resource_offset']
        out+=read_chunk(p['chunk_id'])[local:local+stop-start]
    if len(out)!=size:raise ValueError('buffer page coverage gap')
    return bytes(out)


def main():
    results=[]
    for uid in [5374,7556]:
        pages=resource_pages(uid)
        results.append(dict(uid=uid,pages=len(pages),resource_bytes=sum(p['bytes'] for p in pages),
            first_page=pages[0],last_page=pages[-1],first_bytes=read_resource(uid,0,16).hex()))
    output=ROOT/'resource_reader_validation.json'
    output.write_text(json.dumps(dict(pass_=True,resources=results),indent=2))
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
