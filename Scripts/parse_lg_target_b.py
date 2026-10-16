import struct,json,collections,os
ROOT=r'D:\TLOU2_UE5_8_Codex'; p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak'; b=open(p,'rb').read(); page=9541328; base_rel=0x8e150; # target +0x40
D=json.load(open(ROOT+r'\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
def fnv(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={fnv(x['name']):x for x in D['bones']}; joint=fnv('joint'); nameh=fnv('name')
# entry boundaries from page9 listing (entry198->199->200)
entry198=0x8e120; entry199=0x8e760; entry200=0x8ed98
# target B bytes: stream starts at page-relative base_rel; inspect embedded joint table in entry199 payload
lo=0x898; hi=entry200-base_rel
raw=b[page+base_rel+lo:page+base_rel+hi]
# Find markers and record starts; candidate marker has FNV joint and bone hash at +8
markers=[]
for i in range(0,len(raw)-16):
 if struct.unpack_from('<Q',raw,i)[0]!=joint: continue
 bh=struct.unpack_from('<Q',raw,i+8)[0]
 if bh in by: markers.append(i)
# contiguous groups by delta 48, and all records regardless gap
runs=[]; cur=[]
for m in markers:
 if not cur or m-cur[-1]==48:cur.append(m)
 else:runs.append(cur);cur=[m]
if cur:runs.append(cur)
print('boundaries',hex(lo),hex(hi),'bytes',len(raw),'markers',len(markers),'runs',[(r[0],r[-1],len(r)) for r in runs])
rows=[]
for gi,run in enumerate(runs):
 for ri,m in enumerate(run):
  rec=m-8; bh=struct.unpack_from('<Q',raw,m+8)[0]; bone=by[bh]
  # record layout qwords at rec: pointer/value, name hash, random, joint marker, bone hash, prop hash, packed value, name hash
  # Read from the source address rather than Python's negative slice-relative
  # indices: the first marker is at raw+0 and its record begins eight bytes
  # before the inspected marker window. Stop at the owning resource boundary.
  source_rec=page+base_rel+lo+rec
  source_end=page+base_rel+hi
  words=[struct.unpack_from('<Q',b,source_rec+8*j)[0] if source_rec+8*j+8<=source_end else None for j in range(7)]
  # property qword immediately after bone hash, name qword usually +40 (record+48?) check candidates
  prop=words[4] if len(words)>4 else None
  name_word=words[6] if len(words)>6 else None
  rows.append({'group':gi,'index_in_group':ri,'marker_offset':lo+m,'record_offset':lo+rec,'stride':48,'bone_index':bone['index'],'bone_name':bone['name'],'bone_hash':f'0x{bh:016x}','words':[f'0x{x:016x}' if x is not None else None for x in words],'record_plus40':f'0x{words[5]:016x}' if words[5] is not None else None,'complete_48_byte_record':source_rec+48<=source_end})
print('bones',collections.Counter(r['bone_name'] for r in rows));print('record+40',collections.Counter(r['record_plus40'] for r in rows));print('first',rows[:20])
out={'tool':'parse_lg_target_b.py','source':p,'page9_offset':page,'target_clip':'ellie-prone-lg-aim-strafe-0-fw','target_animal_pointer':{'external_B_relative':'0x8e150','external_B_absolute':page+base_rel},'embedded_region':{'start_relative_to_B':hex(lo),'end_relative_to_B':hex(hi),'start_page_relative':hex(base_rel+lo),'end_page_relative':hex(base_rel+hi),'entry199_resource':'ellie-idle-fb-hr-explosion-fw','boundary_basis':'next page9 resource entry at rel 0x8ed98'},'joint_marker_hash':f'0x{joint:016x}','name_hash':f'0x{nameh:016x}','record_stride':48,'record_count':len(rows),'group_count':len(runs),'groups':[{'group':i,'start_offset':lo+r[0],'end_offset':lo+r[-1]+48,'count':len(r),'bones':collections.Counter(rows2['bone_name'] for rows2 in rows if rows2['group']==i)} for i,r in enumerate(runs)],'rows':rows,'codec_mapping_status':'Bounded joint-marker scan only; transform-channel semantics unresolved.'}
out['target_anim_pointer']=out.pop('target_animal_pointer')
out['codec_mapping_status']='This is a bounded joint-marker region after target B=0x8e150, inside page9 ANIM entry199 (ellie-idle-fb-hr-explosion-fw). Proximity to the primary pointer does not establish primary-clip ownership or transform-channel correspondence. The primary codec +0x30 is a section/table offset 0x120, not a verified descriptor count. Codec group/channel and transform semantics remain unresolved.'
out['record_plus40_counts']=dict(collections.Counter(r.get('record_plus40') for r in rows))
out['bone_counts']=dict(collections.Counter(r['bone_name'] for r in rows))
out['unique_bones']=sorted(set(r['bone_name'] for r in rows))
out['complete_record_count']=sum(r['complete_48_byte_record'] for r in rows)
out['descriptor_index_mapping']={'status':'unresolved','reason':'These 20 marker records lie in a separately bounded ANIM resource; no target codec transform-channel correspondence is established.','codec_payload_pointer_page_relative':'0x41750','section_table_offset_at_plus_0x30':'0x120','descriptor_count_claim':None,'transform_channel_semantics_resolved':False}
json.dump(out,open(ROOT+r'\Content\TLOU2\Reports\lg_target_external_joint_records.json','w'),indent=2)
md=['# Primary lg target external joint records','',f'- Clip: `ellie-prone-lg-aim-strafe-0-fw`.',f'- Target ANIM +0x40 pointer: page9 relative `0x{base_rel:x}` (absolute `{page+base_rel}`).',f'- Embedded joint region: B-relative `0x{lo:x}`..`0x{hi:x}` (next page9 resource boundary `0x{entry200:x}`).',f'- Exact marker: FNV1a64(`joint`) = `{joint:#018x}`; record stride 48 bytes.',f'- Parsed records: `{len(rows)}` in `{len(runs)}` contiguous groups; no descriptor-index guesses are made.', '', '| Group | Records | Bones (counts) |', '|---:|---:|---|']
for i,r in enumerate(runs):md.append(f"| {i} | {len(r)} | "+', '.join(f'{k}×{v}' for k,v in collections.Counter(rows2['bone_name'] for rows2 in rows if rows2['group']==i).items())+' |')
md += ['', 'The primary codec `+0x30` field is the section/table offset `0x120`, not a verified descriptor count. These markers lie in page9 ANIM entry199 (`ellie-idle-fb-hr-explosion-fw`), beyond the resource containing the primary external pointer. Their proximity does not establish ownership by the primary clip. There are 19 complete 48-byte records and one record truncated at the next resource boundary; `record+40` is FNV1a64(`name`) on the 19 complete records. The JSON preserves exact source offsets, bone hashes and bounded qwords. Codec group/channel, transform-channel, temporal ordering and quantization semantics remain unresolved, and no codec descriptor indices are assigned.']
open(ROOT+r'\Content\TLOU2\Reports\LG_TARGET_EXTERNAL_JOINT_RECORDS.md','w',encoding='utf-8').write('\n'.join(md)+'\n')
