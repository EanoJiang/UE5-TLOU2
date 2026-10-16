import json,csv,os
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\animation_source_manifest.json'; out=r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\Reports\ELLIE_ANIMATION_ASSET_CATALOG.csv'; d=json.load(open(p));
with open(out,'w',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['source','chunk','resource_name','resource_type','resource_offset','codec_frame_count','codec_rate_hz','codec_groups','codec_section_offset','raw_header_entry_count','raw_pointer_count','raw_hash_count'])
 for s in d['sources']:
  for c in s.get('chunks',[]):
   # map codec resources in this chunk by resource name (allow duplicates)
   by={}
   for co in c.get('codec',[]): by.setdefault(co.get('resource'),[]).append(co)
   for r in c.get('resources',[]):
    if r.get('type') not in ('ANIM','ANIM_GROUP','ANIM_RAWCHANNELS'): continue
    co=(by.get(r.get('name')) or [None])[0]
    rh=r.get('raw_header') or {}
    w.writerow([s.get('source'),c.get('chunk'),r.get('name'),r.get('type'),r.get('absolute_offset'),co.get('frame_count') if co else '',co.get('sample_rate') if co else '',co.get('group_count') if co else '',co.get('section_offset') if co else '',rh.get('u32_entry_count',''),len(rh.get('page_relative_pointers',[])),len(rh.get('hash_candidates',[]))])
print(out)
