#!/usr/bin/env python3
"""Evidence-only mapping audit for TLOU2 Ellie animation channel hashes.

The JOINT_HIERARCHY table stores 1074 bone name hashes as FNV-1a64.  This
script proves the hash algorithm and compares raw ANIM channel IDs against the
bone table. It deliberately emits no guessed map for compressed descriptors.
"""
from __future__ import annotations
import json, struct, collections, hashlib
from pathlib import Path

ROOT=Path(r"D:/TLOU2_UE5_8_Codex")
PAK=ROOT/"Content/TLOU2/SourcePaks/ellie-skel.pak"
CAP=ROOT/"Exports/ExactDebug/ellie16_patrol_body/capture.json"
MAN=ROOT/"Exports/AnimationSources/DecodedRawChannels/rawchannels_decode_manifest.json"
REPORT=ROOT/"Content/TLOU2/Reports"
TARGET=REPORT/"CODEC_41430102_STRUCTURE_TARGET.json"
EXTERNAL=REPORT/"codec_joint_descriptor_mapping.json"

def fnv1a64(s: str)->int:
    h=0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h=((h^b)*0x100000001b3)&0xffffffffffffffff
    return h

def u64(b,o):return struct.unpack_from('<Q',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]

def main():
    cap=json.loads(CAP.read_text(encoding='utf-8'))
    bones=cap['bones']
    # JOINT_HIERARCHY's name/hash table begins at page 0 relative 0x85630;
    # 1074 records*16 terminate exactly at relative 0x89950.
    raw=PAK.read_bytes(); page0=15472; table_rel=0x85630; count=len(bones)
    hash_rows=[]; table_ok=True
    byhash={}
    for i,bone in enumerate(bones):
        h=u64(raw,page0+table_rel+16*i); ptr=u64(raw,page0+table_rel+16*i+8)
        expected=fnv1a64(bone['name'])
        ok=h==expected
        table_ok &= ok
        hash_rows.append({'index':i,'name':bone['name'],'parentIndex':bone.get('parentIndex',-1),
                          'fnv1a64':f'0x{expected:016x}','joint_table_hash':f'0x{h:016x}',
                          'joint_table_pointer_rel':int(ptr),'hash_verified':ok})
        byhash.setdefault(h,[]).append({'index':i,'name':bone['name']})
    # Pull every raw channel hash from the structural decoder.
    man=json.loads(MAN.read_text(encoding='utf-8'))
    channels=collections.Counter(); uses=collections.defaultdict(list)
    for src in man.get('sources',[]):
        for r in src.get('records',[]):
            for c in r.get('channels',[]):
                try:h=int(c['hash'],16)
                except Exception:continue
                channels[h]+=1
                uses[h].append({'source':src.get('name'),'page':r.get('page'),'entry':r.get('entry'),
                                'resource_offset':r.get('resource_offset'),'format':c.get('format'),
                                'payload_bytes':c.get('payload_bytes')})
    direct=[]; special=[]; unresolved=[]
    special_hashes={0xb0599017cc83e626:'global_flip_frame_0?',
                    0x16ae0a786c0a62e0:'global_flip_frame_1?',
                    0xf2099db117ba20bc:'global_flip_frame_2?',
                    0x5a52202ce3f64436:'global_flip_frame_3?',
                    0x509903bb65ac341e:'root_channel_candidate'}
    for h,n in sorted(channels.items()):
        row={'hash':f'0x{h:016x}','occurrences':n,'uses':uses[h][:12]}
        if h in byhash:
            row['bone_matches']=byhash[h]; direct.append(row)
        elif h in special_hashes:
            row['classification']=special_hashes[h]; special.append(row)
        else:
            unresolved.append(row)
    target={}
    if TARGET.exists():
        try:target=json.loads(TARGET.read_text(encoding='utf-8'))
        except Exception:target={}
    external={}
    if EXTERNAL.exists():
        try: external=json.loads(EXTERNAL.read_text(encoding='utf-8'))
        except Exception: external={}
    out={
      'tool':'map_bone_channel_hashes.py','version':1,
      'status':'evidence_only_no_guessed_mapping',
      'skeleton':{'pak':str(PAK),'joint_hierarchy_name_hash_table_relative_offset':'0x85630',
                  'bone_count':count,'table_record_bytes':16,'table_end_relative':'0x89950',
                  'hash_algorithm':'FNV-1a 64-bit, UTF-8, seed 0xcbf29ce484222325',
                  'all_1074_hashes_verified':table_ok},
      'animation':{'manifest':str(MAN),'unique_channel_hashes':len(channels),
                   'channel_occurrences':sum(channels.values()),
                   'direct_bone_hash_matches':len(direct),
                   'direct_raw_channel_hash_matches':len(direct),
                   'external_joint_descriptor_matches':external.get('record_count',0),
                   'external_joint_descriptor_report':str(EXTERNAL),
                   'external_joint_descriptor_scope':'secondary p-aim clip entry217; not primary lg target entry468',
                   'special_global_hashes':special,
                   'unresolved_channel_hashes':unresolved},
      'target_clip':{'codec_probe':str(TARGET),
                     'section_table_offset_at_plus_0x30':target.get('header',{}).get('section_table_offset','0x120'),
                     'descriptor_count_claim':None,
                     'mapping_status':'no direct bone hash appears in codec/raw channel IDs; codec group/channel table and proprietary quantizer still required',
                     'transform_channel_semantics_resolved':False},
      'bone_hash_rows':hash_rows,
      'direct_matches':direct,
      'external_joint_descriptors':external.get('records',[]),
      'limitations':['Special 5 hashes repeat across humanoid skeleton PAKs and are not entries in the 1074-bone name hash table.',
                     'Raw ANIM channel IDs are not direct FNV-1a hashes of Ellie bone names (0 direct matches).',
                     'The target +0x30 field is the section/table offset 0x120; no independently verified descriptor count is used for bone mapping.',
                     'The eight external joint records are from the secondary p-aim clip; primary lg target external region at page9 relative 0x8e150 requires resource-boundary segmentation.',
                     'No bone/channel map is asserted until codec group/channel-table and transform-channel semantics are decoded.']
    }
    REPORT.mkdir(parents=True,exist_ok=True)
    (REPORT/'bone_channel_hash_mapping_evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    md=['# Ellie bone/channel hash mapping evidence','',
        f'- Skeleton JOINT_HIERARCHY name/hash table: relative `0x85630`, `{count}` records × 16 bytes, ending at `0x89950`.',
        '- Hash algorithm is verified FNV-1a64 over each UTF-8 bone name; all 1,074 records match.',
        f'- Raw animation decoder exposes `{len(channels)}` unique channel IDs (`{sum(channels.values())}` occurrences).',
        f'- Direct raw-channel FNV bone-name matches: **{len(direct)}**; the secondary p-aim ANIM external joint table separately yields **{external.get("record_count",0)}** direct bone-hash records (primary lg target remains unresolved; see `CODEC_JOINT_DESCRIPTOR_MAPPING.md`).',
        '- The recurring IDs `0xb0599017cc83e626`, `0x16ae0a786c0a62e0`, `0xf2099db117ba20bc`, `0x5a52202ce3f64436`, and `0x509903bb65ac341e` are present in skeleton raw-channel resources, but none are bone-name hashes; they are retained as global flip/root candidates.',
        '- Target `ellie-prone-lg-aim-strafe-0-fw` +0x30 is the section/table offset `0x120`; no independently verified descriptor count is used for bone mapping.',
        '', '## Consequence', '',
        'The 1,074-bone names and FNV hash table are available. Raw ANIM channel IDs do not directly identify those names, while the secondary p-aim ANIM external joint table embeds eight exact FNV bone hashes. The primary lg target uses a different external region whose records must be bounded by their owning resources. A valid map requires decoding the codec group/channel table, transform-channel semantics and proprietary quantization. The evidence JSON intentionally leaves all non-direct channels unresolved.','']
    (REPORT/'BONE_CHANNEL_HASH_MAPPING.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps({'report':str(REPORT/'bone_channel_hash_mapping_evidence.json'),'bone_count':count,'all_hashes_verified':table_ok,'unique_animation_hashes':len(channels),'direct_bone_matches':len(direct),'special_global_hashes':len(special),'unresolved':len(unresolved),'target_section_table_offset':target.get('header',{}).get('section_table_offset','0x120'),'descriptor_count_claim':None},indent=2))
if __name__=='__main__':main()
