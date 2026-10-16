#!/usr/bin/env python3
"""Export frame-stride bytes for an ANIM codec block.

ANIM +0x38 is the authoritative codec-header pointer.  For the compact
0x41430102 movement variant, +0x3c low16 gives the per-frame byte stride and
+0x38/+0x48 in the header bound the frame stream.  This exporter writes exact
bytes and bit views only; it intentionally leaves quantizer ranges, channel
semantics, and bone mapping unresolved.
"""
from __future__ import annotations
import csv, hashlib, json, struct, sys
from pathlib import Path

MAGIC=0x41430102
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def cstr(b,o):
    e=b.find(b'\0',o); return b[o:e if e>=0 else len(b)].decode('utf8','replace')
def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    src=Path(sys.argv[1]) if len(sys.argv)>1 else Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
    wanted=sys.argv[2] if len(sys.argv)>2 else 'ellie-prone-lg-aim-strafe-0-fw'
    out=Path(sys.argv[3]) if len(sys.argv)>3 else Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/codec_evidence')
    out.mkdir(parents=True,exist_ok=True)
    b=src.read_bytes(); page_count=u32(b,16); page_table=u32(b,20)
    found=None
    for pi in range(page_count):
        po,psz,pflags=struct.unpack_from('<3I',b,page_table+12*pi)
        ec=u16(b,po+18); starts=[]
        for ei in range(ec):
            no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro
            if rs+16>len(b):continue
            starts.append((rs,ei,ro,cstr(b,po+u64(b,rs)),cstr(b,po+u64(b,rs+8))))
        for rs,ei,ro,name,typ in starts:
            if typ=='ANIM' and name==wanted:
                cp=u64(b,rs+56); q=po+cp
                if q+0x4c<=len(b) and u32(b,q)==MAGIC: found=(pi,po,psz,rs,ei,ro,name,q)
                break
        if found: break
    if not found: raise SystemExit('named ANIM not found or +0x38 is not codec header')
    pi,po,psz,anim,ei,aro,name,q=found
    payload=u32(b,q+8);groups=u16(b,q+12);frames=u16(b,q+14);stride=u16(b,q+0x3c);stream_rel=u32(b,q+0x38);end_rel=u32(b,q+0x48)
    stream=b[q+stream_rel:q+end_rel]; expected=frames*stride
    rows=[]
    for fi in range(frames):
        fr=stream[fi*stride:(fi+1)*stride]
        r={'frame':fi,'time_seconds':fi/30.0,'bytes_hex':fr.hex(),'bits_lsb_first':''.join(f'{x:08b}'[::-1] for x in fr)}
        for j,v in enumerate(fr):r[f'b{j:02d}']=v
        rows.append(r)
    csvp=out/(wanted+'_codec_frame_bytes.csv')
    fields=['frame','time_seconds']+[f'b{i:02d}' for i in range(stride)]+['bytes_hex','bits_lsb_first']
    with csvp.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    doc={'source':str(src),'source_sha256':sha(b),'page':pi,'anim_entry':ei,'anim_name':name,
         'anim_relative':aro,'codec_absolute':q,'codec_page_relative':q-po,
         'codec_sha256':sha(b[q:q+payload]),'magic':hex(MAGIC),'payload_bytes':payload,
         'groups':groups,'frames':frames,'default_rate':struct.unpack_from('<f',b,q+0x1c)[0],
         'sample_period':struct.unpack_from('<f',b,q+0x2c)[0],'frame_stride_bytes':stride,
         'stream_start_relative':hex(stream_rel),'stream_end_relative':hex(end_rel),
         'stream_bytes':len(stream),'expected_stream_bytes':expected,'padding_bytes':len(stream)-expected,
         'interpretation':'Exact frame bytes/bit order only; no quantizer range, channel semantics, bone map, or unit claim.',
         'csv':str(csvp)}
    (out/(wanted+'_codec_frame_bytes.json')).write_text(json.dumps(doc,indent=2),encoding='utf8')
    print(json.dumps(doc,indent=2))
if __name__=='__main__':main()
