"""Resolve codec section palettes from the original JOINT_HIERARCHY header.

The skeleton has eight 32-byte node-group records at hierarchy+0x40. Their
base/count fields partition all 1,074 nodes; transform counts select the 520
original float32 S/Q/T records. Codec section 1 is a separate 108-scalar group.
"""
from __future__ import annotations

import collections
import json
import struct
from pathlib import Path

ROOT = Path(r'D:/TLOU2_UE5_8_Codex')
SKEL = ROOT / 'Content/TLOU2/SourcePaks/ellie-skel.pak'
MOVEMENT = Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
CAP = ROOT / 'Exports/ExactDebug/ellie16_patrol_body/capture.json'
REPORT = ROOT / 'Content/TLOU2/Reports'


def main():
    b = SKEL.read_bytes()
    page, hierarchy = 15472, 15472 + 0x240
    node_count, transform_count, scalar_count = struct.unpack_from('<3H', b, hierarchy + 0x10)
    group_count = b[hierarchy + 0x16]
    header_size, hierarchy_rel = struct.unpack_from('<I', b, hierarchy + 0x20)[0], struct.unpack_from('<I', b, hierarchy + 0x3c)[0]
    parents_start = hierarchy + hierarchy_rel + struct.unpack_from('<I', b, hierarchy + hierarchy_rel + 20)[0]
    parents = [struct.unpack_from('<4i', b, parents_start + 16*i) for i in range(node_count)]
    names = json.loads(CAP.read_text(encoding='utf-8'))['bones']
    groups, nodes = [], []
    transform_cursor = 0
    for gi in range(group_count):
        rec = hierarchy + 0x40 + 32*gi
        words = list(struct.unpack_from('<16H', b, rec))
        base, count, xcount = words[0], words[8], words[9]
        group = {'group_index':gi, 'source_absolute_offset':rec, 'header_relative_offset':hex(rec-hierarchy),
                 'node_base':base, 'node_count':count, 'transform_count':xcount,
                 'transform_stream_index_base':transform_cursor, 'raw_u16':words,
                 'first_node_name':names[base]['name'], 'last_node_name':names[base+count-1]['name'],
                 'parent_group_id_counts':dict(collections.Counter(f'0x{parents[i][0]&0xffffffff:08x}' for i in range(base,base+count)))}
        for local in range(count):
            bi = base + local
            tag = parents[bi][0] & 0xffffffff
            encoded_group = (tag >> 8) & 0xffff
            if encoded_group != gi:
                raise ValueError(('parent group mismatch',bi,gi,tag))
            has_transform = local < xcount
            if has_transform != ((tag >> 30) == 2):
                raise ValueError(('transform flag mismatch',bi,tag,has_transform))
            row = {'bone_index':bi,'bone_name':names[bi]['name'],'skeleton_group':gi,
                   'group_local_node_index':local,'parent_index':parents[bi][1],
                   'raw_parent_group_id':f'0x{tag:08x}', 'has_original_sqt_transform':has_transform,
                   'source_transform_index':transform_cursor+local if has_transform else None,
                   'source_transform_absolute_offset':hierarchy+header_size+48*(transform_cursor+local) if has_transform else None}
            nodes.append(row)
        transform_cursor += xcount
        groups.append(group)
    if len(nodes)!=node_count or transform_cursor!=transform_count:
        raise ValueError(('palette totals',len(nodes),node_count,transform_cursor,transform_count))
    nodes.sort(key=lambda x:x['bone_index'])
    raw = MOVEMENT.read_bytes()
    target = raw[0x95ae20:0x95ae20+0x9c0]
    codec_sections = []
    # Header's seven records: main transforms, scalars, then five remaining
    # original transform groups in skeleton descriptor order.
    source_groups = [0,None,1,2,3,4,5]
    for ci, gi in enumerate(source_groups):
        off=0x30+16*ci
        section_off, packed, stream_off, tail = struct.unpack_from('<4I',target,off)
        section={'codec_section_index':ci,'codec_header_record_offset':hex(off),
                 'payload_section_offset':hex(section_off),'raw_packed_count_flags':f'0x{packed:08x}',
                 'frame_stream_offset':hex(stream_off),'raw_tail':tail}
        if gi is None:
            # Scalar section packs its 108 count into the final header byte;
            # byte +6 is 0x10. This is not a 48-byte bone-transform palette.
            section.update({'kind':'scalar_parameters','scalar_count':target[off+7],
                            'observed_scalar_mode_byte':target[off+6],'bone_base':None,
                            'mapping_evidence':'scalar count equals JOINT_HIERARCHY u16+0x14; no skeleton bone assignment'})
        else:
            count=struct.unpack_from('<H',target,off+6)[0]
            group=groups[gi]
            base=group['node_base']
            if count>group['transform_count']:
                raise ValueError(('codec exceeds original transform palette',ci,count,group))
            section.update({'kind':'sqt_transforms','skeleton_group':gi,'bone_base':base,
                            'codec_record_count':count,'skeleton_group_transform_count':group['transform_count'],
                            'bone_indices':[base+i for i in range(count)],
                            'mapping_evidence':'direct skeleton node-group descriptor base/count and matching parent group IDs'})
            for i in range(count):
                nodes[base+i].update({'codec_section_index':ci,'codec_section_local_record':i,
                                      'codec_section_addressable':True})
        codec_sections.append(section)
    for n in nodes:
        n.setdefault('codec_section_addressable',False)
        if not n['codec_section_addressable']:
            n['non_driven_policy']='retain reference pose; original procedural constraints are outside codec S/Q/T palette'
    checks={'all1074_nodes_partitioned':sum(g['node_count'] for g in groups)==1074,
            'all520_original_transforms_partitioned':sum(g['transform_count'] for g in groups)==520,
            'all_parent_group_ids_match':True,
            'codec_counts_match_direct_skeleton_groups':all(s['codec_record_count']==s['skeleton_group_transform_count'] for s in codec_sections if s['kind']=='sqt_transforms' and s['skeleton_group']!=0),
            'main127_is_prefix_of143_original_transforms':codec_sections[0]['codec_record_count']==127 and groups[0]['transform_count']==143,
            'scalar108_matches_source_header':codec_sections[1]['scalar_count']==scalar_count==108,
            'codec504_bones_addressable':sum(n['codec_section_addressable'] for n in nodes)==504,
            'helper554_nodes_have_no_original_sqt':sum(not n['has_original_sqt_transform'] for n in nodes)==554}
    out={'tool':Path(__file__).name,'source_skeleton':str(SKEL),'hierarchy_absolute_offset':hierarchy,
         'node_count':node_count,'transform_count':transform_count,'scalar_count':scalar_count,
         'skeleton_groups':groups,'target_clip':'ellie-prone-lg-aim-strafe-0-fw',
         'codec_sections':codec_sections,'nodes':nodes,'verification':checks,'pass':all(checks.values()),
         'mapping_rule':'codec local S/Q/T record i maps to direct skeleton group node_base+i; output component byte offsets are 0 scale,16 quaternion,32 translation',
         'note':'Palette addressability does not mean a section has active channels in a particular clip. Empty sections retain the reference pose.'}
    REPORT.mkdir(parents=True,exist_ok=True)
    json_path=REPORT/'SKELETON_CODEC_SECTION_PALETTES.json'
    json_path.write_text(json.dumps(out,indent=2),encoding='utf-8')
    md=['# Direct skeleton-to-codec section palettes','',
        'The original JOINT_HIERARCHY header contains eight 32-byte node-group descriptors at header +0x40. Each descriptor stores node base at u16+0, node count at u16+16, and original transform count at u16+18. These partition all 1,074 named nodes and all 520 stored float32 S/Q/T transforms; every parenting row independently carries the same group index in bits8..23.', '',
        '| Skeleton group | Global bone base | Nodes | Original S/Q/T | First node | Last node |', '|---:|---:|---:|---:|---|---|']
    for g in groups:md.append(f"| {g['group_index']} | {g['node_base']} | {g['node_count']} | {g['transform_count']} | `{g['first_node_name']}` | `{g['last_node_name']}` |")
    md += ['', '| Codec section | Kind | Global bone base | Codec record count |', '|---:|---|---:|---:|']
    for s in codec_sections:md.append(f"| {s['codec_section_index']} | {s['kind']} | {s.get('bone_base','')} | {s.get('codec_record_count',s.get('scalar_count'))} |")
    md += ['', '- Section 1 is 108 scalar parameters, matching skeleton header u16+0x14. It is not a bone palette.',
           '- Main section 0 addresses bones0..126, a prefix of the skeleton main group’s 143 stored transforms. Bones127..142 are reference-pose tails in this target codec.',
           '- Sections2..6 directly address fingers322..359 and face groups360..455,456..554,555..648,649..698.',
           '- 504 bones are addressable by target S/Q/T sections. The remaining570 include16 main-group tail transforms and554 procedural/helper nodes and retain reference pose unless another system drives them.',
           '- An empty clip section supplies no changes even when its palette is addressable.', '',
           'The JSON includes every bone, parent, group, original transform address and codec section/local record mapping.', '',
           '## Verification', '', *[f'- {k}: {v}' for k,v in checks.items()]]
    (REPORT/'SKELETON_CODEC_SECTION_PALETTES.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(json_path),'groups':len(groups),'nodes':len(nodes),'transform_count':transform_cursor,'codec_addressable_bones':sum(n['codec_section_addressable'] for n in nodes),'checks':checks,'pass':out['pass']},indent=2))
    if not out['pass']:raise SystemExit(1)


if __name__=='__main__':main()
