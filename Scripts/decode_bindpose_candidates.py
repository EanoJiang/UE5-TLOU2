import struct, json, os, math, csv

PAK = r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/raw/anim-ellie-player-bindpose/source.pak'
OUT = r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/bindpose_transform_candidates.json'
b = open(PAK, 'rb').read()
magic,hdr,li,lo,pct,pt,fp,fo,*_ = struct.unpack_from('<11I', b, 0)
pages=[struct.unpack_from('<3I',b,pt+i*12) for i in range(pct)]
def u16(o): return struct.unpack_from('<H',b,o)[0]
def u32(o): return struct.unpack_from('<I',b,o)[0]
def u64(o): return struct.unpack_from('<Q',b,o)[0]
def f16(o): return struct.unpack_from('<e',b,o)[0]
def cstr(o):
 e=b.find(b'\0',o); return b[o:e if e>=0 else len(b)].decode('utf8','replace')
rows=[]
for pi,(po,ps,_) in enumerate(pages):
 n=u16(po+18)
 for ei in range(n):
  q=po+20+ei*16; no,ro=struct.unpack_from('<QI',b,q); rs=po+ro
  name=cstr(po+u64(rs)); typ=cstr(po+u64(rs+8))
  if typ!='ANIM_RAWCHANNELS': continue
  base=rs+48; count=u32(base)
  # The TLOU2 raw resource stores its descriptor pointer array after 8 u64 header words.
  ptrs=[u64(base+64+8*i) for i in range(count)]
  for ci,rel in enumerate(ptrs):
   if not (0 < rel < ps):
    rows.append({'raw_entry':ei,'channel':ci,'descriptor_rel':rel,'invalid_pointer':True})
    continue
   d=po+rel
   dtyp=u32(d); payload_rel=u64(d+8)
   if not (0 < payload_rel < ps):
    rows.append({'raw_entry':ei,'channel':ci,'descriptor_rel':rel,'descriptor_type':hex(dtyp),'payload_rel':payload_rel,'invalid_payload_pointer':True})
    continue
   p=po+payload_rel
   vals=[]
   if p+20<=len(b): vals=[f16(p+2*i) for i in range(10)]
   quat=vals[:4] if len(vals)>=4 else []
   qnorm=math.sqrt(sum(x*x for x in quat)) if len(quat)==4 else None
   row={'raw_entry':ei,'channel':ci,'descriptor_rel':rel,'descriptor_type':hex(dtyp),'payload_rel':payload_rel,'half_values':vals,'quat_norm':qnorm}
   if len(vals)>=10:
    row.update(rotation_quat=vals[:4],translation=vals[4:7],scale=vals[7:10],transform_candidate=(qnorm is not None and abs(qnorm-1.0)<0.02))
   rows.append(row)
out={'source':PAK,'raw_channel_resources':sum(1 for pi,(po,ps,_) in enumerate(pages) for ei in range(u16(po+18)) if cstr(po+struct.unpack_from('<Q',b,po+20+ei*16)[0] + 0) == 'ANIM_RAWCHANNELS'), 'candidate_count':len(rows),'candidates':rows}
json.dump(out,open(OUT,'w',encoding='utf-8'),indent=2)
print(json.dumps({'out':OUT,'candidate_count':len(rows),'transform_candidates':sum(bool(x.get('transform_candidate')) for x in rows)},indent=2))
