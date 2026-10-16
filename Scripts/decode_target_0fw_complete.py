"""Decode the bounded original 0-fw S/Q/T clip into portable local transforms.

All dynamic samples are computed from the source codec using the portable
unpack/range/post-log modules. The isolated executable oracle is verification
only. Root RAW candidates and procedurally synthesized motion are excluded.
"""
from __future__ import annotations
import csv,hashlib,json,math,struct
from pathlib import Path
from decode_dynamic_range_python import decode_target_frames
from decode_post_quat_log import unpack_base_quaternions,post_quat_log
from decode_bindpose_static_sections import decode_quat48

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
EVIDENCE=ROOT/'Exports/AnimationSources/DecodedRawChannels/codec_evidence'
EXPORT=ROOT/'Exports/AnimationSources/DecodedOriginal'
REPORT=ROOT/'Content/TLOU2/Reports'
NAME='ellie-prone-lg-aim-strafe-0-fw'
SOURCE=Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak')
SOURCE_OFFSET=0x95ae20
SOURCE_BYTES=0x9c0
EXPECTED_HASH='6d92e0ed0885e10b85a71c38ee0f063394bcd2b85a96308b79306e61eeadf299'

def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def align16(x):return (x+15)&~15

def main():
    blob=(EVIDENCE/(NAME+'_41430102_payload.ndanim.bin')).read_bytes()
    checks={};bounds=[];padding=[];groups=[];tracks={}
    def require(name,condition):
        checks[name]=bool(condition)
        if not condition:raise ValueError(name)
    def bounded(label,start,size):
        require(label+'_in_bounds',0<=start<=start+size<=len(blob))
        bounds.append({'label':label,'offset':start,'bytes':size,'end':start+size})
        return blob[start:start+size]
    def zero_pad(label,start,end):
        value=bounded(label,start,end-start)
        require(label+'_zero',not any(value))
        padding.append({'label':label,'offset':start,'bytes':end-start,'zero':True})
    digest=hashlib.sha256(blob).hexdigest()
    require('payload_sha256_matches_original',digest==EXPECTED_HASH)
    require('payload_magic',u32(blob,0)==0x41430102)
    require('payload_byte_count',u16(blob,8)==len(blob)==SOURCE_BYTES)
    require('source_pak_slice_equals_payload',SOURCE.read_bytes()[SOURCE_OFFSET:SOURCE_OFFSET+SOURCE_BYTES]==blob)
    require('frame_count80',u16(blob,0x0e)==80)
    require('section_count7',u16(blob,0x0c)==7)
    palette=json.loads((REPORT/'SKELETON_CODEC_SECTION_PALETTES.json').read_text(encoding='utf-8'))
    require('palette_verified',palette['pass'])
    nodes={n['bone_index']:n for n in palette['nodes']}
    sections=palette['codec_sections']
    require('skeleton1074nodes',len(nodes)==1074)
    for section in sections:
        hi=0x30+16*section['codec_section_index']
        require('section_header_offset_'+str(section['codec_section_index']),u32(blob,hi)==int(section['payload_section_offset'],16))
        if section['kind']=='sqt_transforms':
            require('section_header_palette_count_'+str(section['codec_section_index']),u16(blob,hi+6)==section['codec_record_count'])
    # Store original 520 S/Q/T reference transforms as a separate static source.
    skel=Path(palette['source_skeleton']).read_bytes();reference=[]
    for bi,node in nodes.items():
        address=node['source_transform_absolute_offset']
        if address is None:continue
        values=struct.unpack_from('<12f',skel,address)
        reference.append({'bone_index':bi,'bone_name':node['bone_name'],'parent_index':node['parent_index'],
            'scale':list(values[:3]),'rotation_xyzw':list(values[4:8]),'translation':list(values[8:11]),
            'source_absolute_offset':address})
    require('reference520_original_sqt',len(reference)==520)

    def get_track(section,local):
        require('section_local_record_bound_'+str(section['codec_section_index'])+'_'+str(local),0<=local<section['codec_record_count'])
        bi=section['bone_indices'][local]
        require('section_bone_map_'+str(bi),bi==section['bone_base']+local and bi in nodes)
        if bi not in tracks:
            tracks[bi]={'bone_index':bi,'bone_name':nodes[bi]['bone_name'],'parent_index':nodes[bi]['parent_index'],
              'section_index':section['codec_section_index'],'section_local_record':local,
              'scale':None,'translation':None,'rotations_xyzw':None,'rotation_channel':'unassigned','source_channels':[]}
        return tracks[bi]

    # Explicitly parse all opcode tables, including empty scalar/face sections.
    programs=[]
    for section in sections:
        start=int(section['payload_section_offset'],16);pos=start;ops=[]
        for operation_index in range(32):
            bounded('opcode_'+str(section['codec_section_index'])+'_'+str(operation_index),pos,2)
            opcode=u16(blob,pos)
            if opcode==0:break
            argc=opcode>>8;args=list(struct.unpack('<'+'H'*argc,bounded('opcode_args_'+str(pos),pos+2,argc*2)))
            ops.append({'offset':pos,'opcode':f'0x{opcode:04x}','arguments':args})
            pos+=2+argc*2
        else:raise ValueError('unterminated section operation program')
        programs.append({'section_index':section['codec_section_index'],'offset':start,'operations':ops,'terminator_offset':pos})
        if section['codec_section_index'] not in (0,2):
            require('section_empty_'+str(section['codec_section_index']),not ops)
            zero_pad('empty_section_'+str(section['codec_section_index']),start,start+16)
        for operation in ops:
            opcode=int(operation['opcode'],16)
            if opcode not in (0x0316,0x0318):continue
            count,base_selector,relative=operation['arguments']
            require('constant_base_selector_'+str(operation['offset']),base_selector==3)
            table=start+relative
            dests=list(struct.unpack('<'+'H'*count,bounded('constant_destinations_'+str(table),table,count*2)))
            sentinel=section['codec_record_count']*48
            active=[d for d in dests if d!=sentinel]
            require('constant_sentinels_tail_'+str(table),dests==active+[sentinel]*(count-len(active)))
            require('constant_padded_count_'+str(table),count%8==0)
            value_start=align16(table+count*2)
            zero_pad('destination_alignment_'+str(table),table+count*2,value_start)
            values=bounded('constant_values_'+str(value_start),value_start,len(active)*6)
            zero_pad('constant_value_alignment_'+str(value_start),value_start+len(values),align16(value_start+len(values)))
            group={'section_index':section['codec_section_index'],'opcode':operation['opcode'],'table_offset':table,
               'padded_count':count,'active_count':len(active),'sentinel_destination':sentinel,
               'destinations':dests,'values_offset':value_start,'active_values_bytes':len(values),'channels':[]}
            for i,dest in enumerate(active):
                local,slot=divmod(dest,48)
                track=get_track(section,local)
                source={'opcode':operation['opcode'],'value_offset':value_start+i*6,'destination':dest,'slot':slot}
                if opcode==0x0316:
                    require('half3_component_slot_'+str(dest),slot in (0,32))
                    kind='scale' if slot==0 else 'translation'
                    require('constant_unique_'+str(track['bone_index'])+'_'+kind,track[kind] is None)
                    track[kind]=list(struct.unpack_from('<3e',values,i*6))
                else:
                    require('quat_component_slot_'+str(dest),slot==16)
                    require('constant_unique_'+str(track['bone_index'])+'_quaternion',track['rotations_xyzw'] is None)
                    q=decode_quat48(values[i*6:i*6+6])['quaternion_xyzw']
                    track['rotations_xyzw']=[q[:] for _ in range(80)]
                    track['rotation_channel']='constant_quat48'
                    kind='rotation'
                source['kind']=kind;track['source_channels'].append(source)
                group['channels'].append({'bone_index':track['bone_index'],'bone_name':track['bone_name'],**source})
            groups.append(group)
    expected_a=[0x0316,0x0318,0x060b,0x041b,0x041d,0x0410]
    require('main_operation_program_exact',[int(o['opcode'],16) for o in programs[0]['operations']]==expected_a)
    require('finger_operation_program_exact',[int(o['opcode'],16) for o in programs[2]['operations']]==[0x0316,0x0318])
    expected_args=[[16,3,0x40],[8,3,0xc0],[0x8004,3,0xf0,0,0,15],[0x8004,3,0x100,0],[4,3,0x150,0],[4,3,0x170,0]]
    require('main_operation_arguments_exact',[o['arguments'] for o in programs[0]['operations']]==expected_args)
    range_result=decode_target_frames(blob)
    require('dynamic_stream_offset',range_result['frame_stream_start']==0x500)
    require('dynamic_frame_stride',range_result['frame_stride']==15)
    require('dynamic_widths',range_result['widths']==[33,34,34,12])
    bounded('dynamic_frame_stream',0x500,80*15)
    require('dynamic_unused7bits_zero',all(blob[0x500+15*i+14]&127==0 for i in range(80)))
    padding.append({'label':'dynamic_frame_tail_bits','bits_per_frame':7,'frames':80,'zero':True})
    bases=unpack_base_quaternions(bounded('post_log_base_metadata',0x270,32),4)
    destinations=list(struct.unpack('<8H',bounded('dynamic_scatter_padded_table',0x290,16)))
    require('dynamic_destinations_exact',destinations==[1552,1648,1840,1744]+[127*48]*4)
    require('dynamic_sentinel_tail',destinations[4:]==[127*48]*4)
    dynamic_bones=[]
    for lane,dest in enumerate(destinations[:4]):
        local,slot=divmod(dest,48)
        require('dynamic_rotation_slot_'+str(lane),slot==16)
        track=get_track(sections[0],local)
        require('dynamic_rotation_no_constant_conflict_'+str(local),track['rotations_xyzw'] is None)
        track['rotations_xyzw']=[post_quat_log(row['range_vectors'][lane],bases[lane]) for row in range_result['rows']]
        track['rotation_channel']='original_dynamic_unpack_range_post_quat_log'
        track['source_channels'].append({'kind':'rotation','lane':lane,'destination':dest,'stream_offset':0x500,
            'frame_stride':15,'unpack_widths_offset':0x210,'range_metadata_offset':0x220,'post_log_metadata_offset':0x270})
        dynamic_bones.append(track['bone_index'])
    require('dynamic_bone_indices',[32,34,38,36]==dynamic_bones)
    oracle=json.loads((EVIDENCE/'native_leaf_range_oracle.json').read_text(encoding='utf-8'))
    require('native_oracle80_frames',len(oracle['rows'])==80)
    native_unpack_exact=native_range_exact=native_quat_exact=0
    for row,native in zip(range_result['rows'],oracle['rows']):
        native_unpack_exact+=row['unpacked_u64']==native['native_unpacked_u64']
        native_range_exact+=row['range_vectors']==native['range_vectors']
        for lane,bi in enumerate(dynamic_bones):
            q=tracks[bi]['rotations_xyzw'][row['frame']]
            native_quat_exact+=struct.pack('<4f',*q)==struct.pack('<4f',*native['quaternions_xyzw'][lane])
    require('native_unpack80_bit_exact',native_unpack_exact==80)
    require('native_range80_bit_exact',native_range_exact==80)
    require('native_post_log320_bit_exact',native_quat_exact==320)
    ordered=[tracks[bi] for bi in sorted(tracks)]
    require('driven26_bones',len(ordered)==26)
    require('static_rotation22_bones',sum(t['rotation_channel']=='constant_quat48' for t in ordered)==22)
    require('main7_finger19',sum(t['section_index']==0 for t in ordered)==7 and sum(t['section_index']==2 for t in ordered)==19)
    require('root_not_driven',0 not in tracks)
    require('all_tracks_complete_local_sqt',all(t['scale'] is not None and t['translation'] is not None and len(t['rotations_xyzw'] or [])==80 for t in ordered))
    require('all_outputs_finite',all(math.isfinite(v) for t in ordered for values in [t['scale'],t['translation'],*[q for q in t['rotations_xyzw']]] for v in values))
    for track in ordered:
        track['local_space']=True
        track['frame_count']=80
    # The resource has a nonzero 16-byte trailer. Preserve it as opaque metadata,
    # never claim that it is zero alignment padding or a root-motion channel.
    footer=bounded('opaque_codec_footer',0x9b0,16)
    fps=30.0
    frames=[{'frame':fi,'time_seconds':fi/fps,'local_sqt':[
       {'bone_index':t['bone_index'],'bone_name':t['bone_name'],'scale':t['scale'],
        'rotation_xyzw':t['rotations_xyzw'][fi],'translation':t['translation']} for t in ordered]} for fi in range(80)]
    validation={'pass':all(checks.values()),'checks':checks,'bounds':bounds,'padding':padding,
      'native_comparison':{'unpack_frames_bit_exact':native_unpack_exact,'range_frames_bit_exact':native_range_exact,
       'quaternion_float4_bit_exact':native_quat_exact,'quaternions_compared':320,'max_dynamic_component_error':0.0},
      'constant_quat48_validation':'Established 2-bit swap + 16/15/15 unsigned bias layout; independent bindpose/skeleton and native constant guard evidence. Static outputs are retained at decoder precision rather than forced into native approximate-sqrt rounding.',
      'clip_footer':{'offset':0x9b0,'bytes':16,'hex':footer.hex(),'interpretation':'opaque source metadata; not treated as padding, bone transform, or root channel'}}
    result={'schema':'tlou2.original-local-sqt.v1','clip_name':NAME,'source':{'package':str(SOURCE),'codec_absolute_offset':SOURCE_OFFSET,
       'codec_payload_bytes':len(blob),'codec_payload_sha256':digest,'source_payload_file':str(EVIDENCE/(NAME+'_41430102_payload.ndanim.bin'))},
      'coordinates':{'source_units':'meters','up_axis':'Y','space':'local parent-relative S/Q/T','quaternion_order':'xyzw','conversion_applied':False},
      'timing':{'frame_count':80,'frame_rate':fps,'fps':fps,'sample_period_seconds':1/fps,'last_key_time_seconds':79/fps,
        'key_span_seconds':79/fps,'80_sample_playback_span_seconds':80/fps,'codec_normalized_sample_period':struct.unpack_from('<f',blob,0x24)[0],
        'codec_normalized_sample_rate':struct.unpack_from('<f',blob,0x28)[0],'playback_note':'30 Hz delivery timebase. Codec normalized period1/79 describes its normalized frame range, not a79Hz playback claim.'},
      'frame_count':80,'fps':fps,'driven_bone_count':26,'dynamic_bone_indices':dynamic_bones,
      'undriven_bone_policy':{'policy':'retain rig reference pose','undriven_node_count':1074-26,'all_node_count':1074,
        'source_reference_sqt_count':520,'procedural_or_helper_nodes_without_stored_sqt':554,
        'source_skeleton':palette['source_skeleton'],'section_palette_report':str(REPORT/'SKELETON_CODEC_SECTION_PALETTES.json'),
        'note':'The separate corrected rig reconstructs reference transforms for nodes without a stored original S/Q/T. This clip does not synthesize their procedural constraints.'},
      'root_motion':{'root_bone_index':0,'root_driven_by_this_clip':False,'trajectory_exported_from_this_clip':False,
        'policy':'root retains reference pose; no independent ANIM_RAWCHANNELS root candidate is mixed into this clip'},
      'tracks':ordered,'frames':frames,'reference_pose_original_sqt':reference,'operation_programs':programs,'constant_groups':groups,'validation':validation,
      'scope_note':'Original 26 driven S/Q/T bones, including 4 animated rotations. This movement clip is source decoded; it has not been proven to be the exact animation playing in the character-gallery capture.'}
    EXPORT.mkdir(parents=True,exist_ok=True)
    output=EXPORT/(NAME+'.json');output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    csv_path=output.with_suffix('.csv')
    with csv_path.open('w',newline='',encoding='utf-8-sig') as handle:
        writer=csv.writer(handle);writer.writerow(['clip_name','frame','time_seconds','bone_index','bone_name','section_index','section_local_record','rotation_channel','sx','sy','sz','qx','qy','qz','qw','tx_m','ty_m','tz_m'])
        for fi in range(80):
            for t in ordered:writer.writerow([NAME,fi,fi/fps,t['bone_index'],t['bone_name'],t['section_index'],t['section_local_record'],t['rotation_channel'],*t['scale'],*t['rotations_xyzw'][fi],*t['translation']])
    (REPORT/'TARGET_0FW_COMPLETE_DECODE_VALIDATION.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    readme=['# Original 0-fw animation decode','',
      f'`{NAME}.json` and `.csv` contain 80 samples at 30 Hz in original local parent-relative S/Q/T, with translation in meters and Y up. JSON quaternion order is XYZW. No coordinate conversion has been applied.','',
      '- Driven bones: 26 (7 main/right-arm bones and 19 finger bones).',
      '- Dynamic bones: 32 r_clavicle, 34 r_shoulder, 38 r_wrist, 36 r_elbow.',
      '- Other 22 driven rotations, all 26 scales, and all 26 translations are decoded constants. Static rotations repeat across all 80 samples.',
      '- Other 1048 skeleton nodes retain the corrected rig reference pose. The source skeleton stores 520 S/Q/T transforms; 554 helper/procedural nodes require the rig reference reconstruction.',
      '- Root bone 0 is not driven. No independent RAW root candidate, arbitrary trajectory, motion fitting, or synthetic motion is included.',
      '- Last key time is 79/30 seconds. The codec period 1/79 is a normalized timing field; delivered playback uses 30 Hz.','',
      '## Verified source decode','',
      '- Payload SHA256: `'+digest+'`.',
      '- Source package slice at 0x95ae20 equals the preserved 2496-byte payload exactly.',
      '- Portable bit unpack: 80/80 native frames match bit for bit.',
      '- Portable range decode: 80/80 native frames match every float32 component.',
      '- Portable quaternion post-log: 320/320 native float4 quaternions match bit for bit; maximum component error 0.',
      '- Every active destination is bounded by its original section palette, with the correct S/Q/T component slot. Sentinel destinations are accepted only in table tails and are excluded from driven tracks.',
      '- Constant table alignment bytes, constant value alignment bytes, empty section blocks, and 7 unused tail bits in all 80 dynamic frames are zero. The 16-byte nonzero footer is preserved as opaque metadata.',
      '- All 26 output tracks contain scale, translation, and 80 finite quaternions.','',
      '## JSON handoff','',
      '`tracks` contains `{bone_index,bone_name,scale,translation,rotations_xyzw:[80 quaternion]}` plus parent/section/source evidence. `frames` provides explicit per-frame local S/Q/T. `reference_pose_original_sqt` stores the 520 original reference transforms separately; these are not extra animation channels. The CSV has 2080 data rows (80×26).','',
      'The native oracle only verifies the independently computed portable outputs. The decoder does not load or execute game code. Scripts/decode_dynamic_range_python.py, decode_post_quat_log.py, and decode_bindpose_static_sections.py supply the established arithmetic.','',
      'This source movement clip is not independently proven to be the animation playing in the captured character-gallery screen. Full visual fidelity additionally requires the corrected model rig, materials, gallery camera/light/UI, and export/import validation.']
    (EXPORT/'README.md').write_text('\n'.join(readme)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(output),'csv':str(csv_path),'tracks':len(ordered),'frames':80,'csv_rows':80*len(ordered),'native_comparison':validation['native_comparison'],'checks':len(checks),'pass':validation['pass']},indent=2))

if __name__=='__main__':main()
