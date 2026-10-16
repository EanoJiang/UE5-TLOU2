import json,struct
from pathlib import Path
p=Path(r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\Reports\lg_target_288_descriptor_bone_candidates.json');d=json.loads(p.read_text()); pak=Path(r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak'); b=pak.read_bytes(); page=9541328; # build page9 resource starts
h,hd,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); po,ps,_=struct.unpack_from('<3I',b,pt+12*9); ec=struct.unpack_from('<H',b,po+18)[0]
def cs(o):e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else''
starts=[]
for ei in range(ec):
 no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro; typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0]);name=cs(po+struct.unpack_from('<Q',b,rs)[0]);starts.append((ro,ei,typ,name))
starts.sort()
for row in d['rows']:
 rel=row['page_relative_marker_offset']; c=[x for x in starts if x[0]<=rel];
 if c:
  ro,ei,typ,name=c[-1]; row['page9_resource_entry']=ei;row['page9_resource_start_relative']=hex(ro);row['page9_resource_type']=typ;row['page9_resource_name']=name
# summary counts entries
from collections import Counter
d['page9_resource_entry_counts']=dict(Counter(str(r.get('page9_resource_entry')) for r in d['rows']))
p.write_text(json.dumps(d,indent=2),encoding='utf-8')
