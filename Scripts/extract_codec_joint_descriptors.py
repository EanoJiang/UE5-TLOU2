#!/usr/bin/env python3
"""Extract direct bone-hash descriptors from the external ANIM stream.

For the selected secondary p-aim movement clip, ANIM field +0x38 points at a short external
joint descriptor table. Each 48-byte record has a qword marker `FNV1a64("joint")`
at record+8 and an FNV1a64 bone-name hash at record+16. This is direct evidence
for descriptor->bone identity; no quantized sample values are interpreted here.
"""
import json,struct,hashlib
from pathlib import Path
ROOT=Path(r'D:/TLOU2_UE5_8_Codex'); PAK=ROOT/'Content/TLOU2/SourcePaks/Animations/anim-ellie-player-movement.pak'
if not PAK.exists(): PAK=Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
CAP=ROOT/'Exports/ExactDebug/ellie16_patrol_body/capture.json'; REPORT=ROOT/'Content/TLOU2/Reports'
# page 9 from movement PAK; selected ANIM's external A pointer 0xac3b0
def fnv(s):
 h=0xcbf29ce484222325
 for b in s.encode():h=((h^b)*0x100000001b3)&0xffffffffffffffff
 return h
def u64(b,o):return struct.unpack_from('<Q',b,o)[0]
def main():
 D=json.loads(CAP.read_text()); by={fnv(x['name']):x for x in D['bones']}
 b=PAK.read_bytes(); page_off=9541328; ext_rel=0xac3b0; ext=b[page_off+ext_rel:page_off+ext_rel+0x180]
 joint=fnv('joint'); rows=[]
 # expected first external table has 8 records at marker offsets 8 + 48*i
 for marker in range(8,0x180,48):
  if marker+24>len(ext) or u64(ext,marker)!=joint: continue
  bh=u64(ext,marker+8); bone=by.get(bh)
  rows.append({'external_stream':'A','page_index':9,'page_offset':page_off,
    'stream_pointer_relative':ext_rel,'record_offset':marker-8,'joint_marker_offset':marker,
    'record_stride':48,'joint_hash':f'0x{joint:016x}','bone_hash':f'0x{bh:016x}',
    'bone_index':bone['index'] if bone else None,'bone_name':bone['name'] if bone else None,
    'word_before_marker':f'0x{u64(ext,marker-8):016x}',
    'word_after_bone':f'0x{u64(ext,marker+16):016x}',
    'word_after_property':f'0x{u64(ext,marker+24):016x}'})
 out={'tool':'extract_codec_joint_descriptors.py','version':1,'status':'direct_bone_hash_evidence',
      'source_pak':str(PAK),'clip':'ellie-prone-p-aim-strafe-0-fw',
      'anim_page_index':9,'anim_external_field':'ANIM +0x38 / field pointer',
      'page_offset':page_off,'external_pointer_relative':hex(ext_rel),'external_stream_bytes':len(ext),
      'record_count':len(rows),'record_stride':48,'joint_hash':f'0x{joint:016x}',
      'records':rows,'mapping_confidence':'direct FNV1a64 bone-name hash match',
      'relation_to_primary_target':'This is a secondary p-aim clip (entry217), not the primary CODEC_41430102 target ellie-prone-lg-aim-strafe-0-fw (entry468).',
      'primary_target_note':'Primary lg target uses ANIM +0x38=0x41750 and +0x40=0x8e150; codec +0x30 is section/table offset 0x120. No descriptor count or transform-channel-to-bone order is independently established.',
      'limitations':['This table identifies the eight external joint descriptors attached to the selected ANIM resource.',
                     'It does not decode compressed frame samples in the 0x41430102 payload.',
                     'Other external tables use different layouts and require boundary discovery before inclusion.']}
 REPORT.mkdir(parents=True,exist_ok=True); (REPORT/'codec_joint_descriptor_mapping.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 lines=['# Direct codec joint descriptor mapping','',f'- Clip: `ellie-prone-p-aim-strafe-0-fw`.',f'- External stream pointer: page 9 relative `0x{ext_rel:x}`; table bytes `0x180`.',f'- Marker: FNV1a64(`joint`) = `{joint:#018x}`; record stride 48 bytes.', '', '| Record | Bone index | Bone name | Bone hash |', '|---:|---:|---|---|']
 for i,r in enumerate(rows):lines.append(f"| {i} | {r['bone_index']} | `{r['bone_name']}` | `{r['bone_hash']}` |")
 lines += ['', 'These eight records contain exact FNV1a64 bone-name hashes. They establish record identity for the secondary p-aim clip only; transform-channel, temporal ordering and compressed sample semantics remain unresolved.', '', '- This secondary table is ANIM entry217, not primary lg target entry468.', '- Primary lg target uses ANIM +0x38=`0x41750` and +0x40=`0x8e150`; codec `+0x30` is section/table offset `0x120`. No descriptor count or transform-channel-to-bone order is independently established.']
 (REPORT/'CODEC_JOINT_DESCRIPTOR_MAPPING.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); print(json.dumps({'report':str(REPORT/'codec_joint_descriptor_mapping.json'),'records':len(rows),'bones':[r['bone_name'] for r in rows]},indent=2))
if __name__=='__main__':main()

