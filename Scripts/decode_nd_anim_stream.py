#!/usr/bin/env python3
"""Inventory and extract Naughty Dog ANIM/ANIM_RAWCHANNELS resources.

The animation files used by TLOU2 are regular Naughty Dog page packages with a
16-byte stream prefix in ``animstream97/*.stm``.  The game serializer places a
small ``0x41430102`` animation codec header and quantized channel payloads in
each page.  This utility deliberately keeps the original bytes byte-for-byte,
but exposes the package/chunk/resource layout in JSON and writes each codec
payload as a standalone ``.ndanim.bin``.  That gives Blender/UE tooling a
stable handoff while the proprietary quantizer is being decoded.

It is safe to run on either a direct actor97 ``.pak`` or a streamed ``.stm``.
No game executable is required.
"""
from __future__ import annotations
import argparse, json, math, os, struct, hashlib, re, sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

MAGICS = {2681, 2685, 68217, 2147486329, 68221}
CODEC_MAGIC = 0x41430102  # bytes 02 01 43 41 seen in all ANIM payloads

def u16(b: bytes, o: int) -> int:
    return struct.unpack_from('<H', b, o)[0]
def i16(b: bytes, o: int) -> int:
    return struct.unpack_from('<h', b, o)[0]
def u32(b: bytes, o: int) -> int:
    return struct.unpack_from('<I', b, o)[0]
def i32(b: bytes, o: int) -> int:
    return struct.unpack_from('<i', b, o)[0]
def u64(b: bytes, o: int) -> int:
    return struct.unpack_from('<Q', b, o)[0]
def f32(b: bytes, o: int) -> float:
    return struct.unpack_from('<f', b, o)[0]
def cstr(b: bytes, o: int) -> str:
    if o < 0 or o >= len(b): return ''
    e = b.find(b'\0', o)
    if e < 0: e = len(b)
    return b[o:e].decode('utf-8', 'replace')
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def finite(v: float) -> Optional[float]:
    return float(v) if math.isfinite(v) else None

class Pak:
    def __init__(self, data: bytes, prefix: int = 0):
        self.data = data[prefix:]
        self.prefix = prefix
        self.pages: List[Tuple[int,int,int]] = []
        self.resources: List[Dict[str,Any]] = []
        self.valid = False
        self.parse()

    def parse(self):
        b = self.data
        if len(b) < 64: return
        try:
            vals = struct.unpack_from('<11I', b, 0)
            magic, hdr, login_idx, login_off, page_count, page_table, fix_pages, fix_off, unk5, unk6, unk7 = vals
            if magic not in MAGICS or page_count <= 0 or page_count > 4096: return
            if page_table + page_count*12 > len(b): return
            self.header = dict(magic=magic, header_size=hdr, login_table_idx=login_idx,
                               login_table_offset=login_off, page_count=page_count,
                               page_table=page_table, fixup_page_count=fix_pages,
                               fixup_offset=fix_off, unknown=[unk5,unk6,unk7])
            self.pages = [struct.unpack_from('<3I', b, page_table + 12*i) for i in range(page_count)]
            self.valid = True
            # A TLOU2 page header has 0xdeadbeefdeadbeef at +0 and entry count
            # at +0x12.  Some older packages use the same entry shape.
            for pi,(po,ps,_) in enumerate(self.pages):
                if po + 20 > len(b): continue
                try: n = u16(b, po+18)
                except Exception: continue
                if n > 10000: continue
                for ei in range(n):
                    q = po + 20 + 16*ei
                    if q + 16 > len(b): break
                    name_off, res_off = struct.unpack_from('<QI', b, q)
                    rs = po + res_off
                    if rs + 16 > len(b): continue
                    try:
                        item_name = cstr(b, po + name_off)
                        type_off = u64(b, rs+8)
                        item_type = cstr(b, po + type_off)
                    except Exception:
                        item_name = item_type = ''
                    self.resources.append(dict(page=pi, page_offset=po, entry=ei,
                                               name=item_name, type=item_type,
                                               relative_offset=res_off, absolute_offset=rs))
        except (struct.error, ValueError):
            self.valid = False

    def codec_records(self) -> List[Dict[str,Any]]:
        """Find codec headers in this package and associate the nearest ANIM resource."""
        b = self.data
        hits=[]; start=0
        while True:
            p = b.find(struct.pack('<I', CODEC_MAGIC), start)
            if p < 0: break
            # False positives are very uncommon; check the channel/frame fields.
            if p + 52 <= len(b):
                # ANIM codec header is mixed-width.  +0x08 is the encoded
                # payload byte count, +0x0c/+0x0e are 16-bit group/frame
                # counts.  The ANIM resource itself carries the channel/bone
                # group count; do not mistake the payload size for channels.
                payload_size = u16(b,p+8); g = u16(b,p+12); fc = u16(b,p+14)
                dt = f32(b,p+36)
                if 0 < payload_size <= len(b) and 0 < fc < 100000 and (0 < dt < 10 or not math.isfinite(dt)):
                    hits.append((p,payload_size,g,fc,dt))
            start=p+4
        out=[]
        anims=[r for r in self.resources if r.get('type') in ('ANIM','ANIM_RAWCHANNELS')]
        for p,payload_size,g,fc,dt in hits:
            # Prefer the ANIM resource whose page contains the header and whose
            # resource start follows it.  For stream chunks this is page 0.
            page = next((i for i,(po,ps,_) in enumerate(self.pages) if po <= p < po+ps), None)
            cand=[r for r in anims if r['page']==page and r['absolute_offset']>=p]
            r=min(cand,key=lambda x:x['absolute_offset']) if cand else None
            # The compact header fields are useful even before quantized tracks
            # are decoded.  Keep both integer and float interpretations.
            resource_channels = None
            if r:
                # TLOU2 ANIM resources begin with two u32 values after the
                # standard 48-byte ResItem header.  The second is the logical
                # channel/group count (24 for Dina body chunks, 57 for facial).
                try: resource_channels = u32(b, int(r['absolute_offset']) + 52)
                except Exception: resource_channels = None
            rec=dict(offset=p, page=page, resource=(r['name'] if r else None),
                     resource_offset=(r['absolute_offset'] if r else None),
                     codec_magic=f'0x{CODEC_MAGIC:08x}', channel_count=resource_channels,
                     codec_payload_size=payload_size, resource_channel_count=resource_channels,
                     resource_type=(r['type'] if r else None),
                     group_count=g, frame_count=fc, sample_period=finite(dt),
                     sample_rate=(1.0/dt if dt and math.isfinite(dt) and dt>0 else None),
                     header_u32=[u32(b,p+4*i) for i in range(12)],
                     header_sha256=sha256(b[p:min(len(b),p+64)]))
            # The codec header is mixed-width.  +0x30 is the offset of the
            # first section/table (0x120 in the target and one-frame bindpose
            # codecs), not a descriptor count.  The old reader exposed its
            # decimal value (288) as ``descriptor_count``; that was an offset
            # coincidence and made downstream reports look like a bone count.
            rec.update(
                frame_count_alt=u16(b,p+34),
                sample_rate_alt=finite(f32(b,p+40)),
                legacy_data_offset_field_18=u32(b,p+24),
                legacy_section_field_14=u32(b,p+20),
                frame_period_alt=finite(f32(b,p+44)),
                section_offset=u32(b,p+48),
                header_flags=u32(b,p+52),
                stream_offset=u32(b,p+56),
                packed_stride=u32(b,p+60),
                channel_table_offset=u32(b,p+64),
                external_field=u32(b,p+68),
                data_end=u32(b,p+72),
                section_offset_semantics='codec section/table offset; descriptor count unresolved'
            )
            out.append(rec)
        return out

    def enrich_raw_channels(self):
        """Attach a structural summary for every ANIM_RAWCHANNELS resource.

        The first words are intentionally left as integers: the resource uses
        pointer fixups and 64-bit channel hashes, and interpreting these as
        bone transforms before the proprietary quantizer is understood would
        produce misleading poses.
        """
        b=self.data
        for r in self.resources:
            if r.get('type')!='ANIM_RAWCHANNELS': continue
            rs=int(r['absolute_offset']); q=rs+48
            if q+16>len(b): continue
            vals=[]
            for i in range(32):
                if q+8*i+8>len(b): break
                vals.append(u64(b,q+8*i))
            po=int(r.get('page_offset',0)); plen=next((int(x[1]) for j,x in enumerate(self.pages) if j==r.get('page')),0)
            pointers=[]; hashes=[]
            for v in vals:
                # A page-relative pointer resolves inside the page.  Ignore
                # sentinel 0x00012345 fields used by ResItem padding.
                if 0 < v < plen and po+v < len(b): pointers.append(int(v))
                elif v not in (0,0x0001234500000000,0x0001234500012345): hashes.append(f'0x{v:016x}')
            r['raw_header']={'u32_entry_count':u32(b,q),
                             'u32_second':u32(b,q+4),
                             'u64_words':[f'0x{x:016x}' for x in vals],
                             'page_relative_pointers':pointers,
                             'hash_candidates':hashes}

def split_stream(data: bytes) -> List[Tuple[int,int,int]]:
    """Return (pak_start, pak_end, prefix_start) for each ANIMMAGICSTR block."""
    starts=[]; p=0; sig=b'ANIMMAGICSTR'
    while True:
        i=data.find(sig,p)
        if i<0: break
        # Every block has a 4-byte hash immediately before the 12-byte marker;
        # the PAK header starts after that 16-byte prefix.
        starts.append(max(0,i-4)); p=i+len(sig)
    out=[]
    for j,s in enumerate(starts):
        e=starts[j+1] if j+1<len(starts) else len(data)
        if e-s >= 20: out.append((s+16,e,s))
    return out

def half_stats(data: bytes) -> Dict[str,Any]:
    vals=[]
    # Raw channel quantization uses half values.  Report a conservative sample
    # to aid decoder work; never present this as decoded transforms.
    for o in range(0, len(data)-1, 2):
        h=struct.unpack_from('<e',data,o)[0]
        if math.isfinite(h) and abs(h) < 10000: vals.append(float(h))
    if not vals: return dict(count=0)
    return dict(count=len(vals), min=min(vals), max=max(vals), mean=sum(vals)/len(vals),
                zero_fraction=sum(1 for v in vals if v==0.0)/len(vals))

def inspect_one(path: Path, outdir: Path) -> Dict[str,Any]:
    raw=path.read_bytes(); is_stream=path.suffix.lower()=='.stm'
    blocks=split_stream(raw) if is_stream else [(0,len(raw),0)]
    paks=[]; source_name=path.name
    for ci,(ps,pe,prefix) in enumerate(blocks):
        pak_bytes=raw[ps:pe]
        pak=Pak(pak_bytes)
        if not pak.valid:
            # A direct PAK has no prefix; stream block bytes already stripped.
            paks.append(dict(chunk=ci,start=ps,end=pe,size=len(pak_bytes),valid=False))
            continue
        chunk_name=f'{path.stem}.chunk{ci:04d}' if is_stream else path.stem
        chunk_dir=outdir/'raw' / chunk_name
        chunk_dir.mkdir(parents=True,exist_ok=True)
        (chunk_dir/'source.pak').write_bytes(pak_bytes)
        pak.enrich_raw_channels()
        codec=pak.codec_records()
        payloads=[]
        for ai,c in enumerate(codec):
            p=int(c['offset']); end=int(c['resource_offset'] or min(len(pak.data),p+0x100000))
            if end<=p: end=min(len(pak.data),p+0x100000)
            blob=pak.data[p:end]
            fn=f'codec_{ai:02d}.ndanim.bin'; (chunk_dir/fn).write_bytes(blob)
            c['payload_file']=str(Path('raw')/chunk_name/fn).replace('\\','/')
            c['payload_blob_size']=len(blob); c['payload_sha256']=sha256(blob)
            c['half_stats']=half_stats(blob)
            payloads.append(c)
        paks.append(dict(chunk=ci,start=ps,end=pe,size=len(pak_bytes),valid=True,
                         page_count=len(pak.pages),resources=pak.resources,
                         codec=payloads,source_pak=str(Path('raw')/chunk_name/'source.pak').replace('\\','/'),
                         sha256=sha256(pak_bytes)))
    return dict(source=source_name,path=str(path),size=len(raw),kind='stm' if is_stream else 'pak',
                sha256=sha256(raw),chunks=paks,
                decode_status='container and codec metadata decoded; proprietary channel quantizer preserved')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('inputs',nargs='+'); ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for pat in args.inputs:
        paths=[]
        for x in Path().glob(pat) if not os.path.isabs(pat) else []: paths.append(x)
        if os.path.isdir(pat): paths=[p for p in Path(pat).rglob('*') if p.suffix.lower() in ('.stm','.pak')]
        elif os.path.isfile(pat): paths=[Path(pat)]
        else: paths=[Path(x) for x in __import__('glob').glob(pat,recursive=True)]
        for p in paths:
            try: reports.append(inspect_one(p,out))
            except Exception as e: reports.append(dict(source=p.name,path=str(p),error=repr(e)))
    manifest={'tool':'decode_nd_anim_stream.py','version':1,'sources':reports}
    (out/'animation_source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Human-readable summary for the UE validation report.
    lines=['# Naughty Dog animation source extraction','',f'Sources inspected: {len(reports)}','',
           'This report decodes the PAK/STM container, codec header, channel/frame counts, and preserves each quantized payload as `.ndanim.bin`. The proprietary ANIM_RAWCHANNELS quantizer remains byte-preserved for a later reader.','',
           '| Source | Chunks | Codec payloads | Channels/frame range |','|---|---:|---:|---|']
    for r in reports:
        cs=r.get('chunks',[]); codecs=[c for ch in cs for c in ch.get('codec',[])]
        ranges=', '.join(f"{c.get('channel_count')}/{c.get('frame_count')}" for c in codecs[:4]) or 'none'
        lines.append(f"| `{r.get('source')}` | {len(cs)} | {len(codecs)} | {ranges} |")
    (out/'ANIMATION_DECODE_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'sources':len(reports),'manifest':str(out/'animation_source_manifest.json')},indent=2))
if __name__=='__main__': main()
