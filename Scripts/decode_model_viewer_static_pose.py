"""Decode the original gallery Ellie Patrol static S/Q/T and scalar pose.

Uses PAK cross-page pointer fixups, not nearest-resource association. Constant
half3 and Quat48 formats are already independently checked against bindpose.
Float3/scalar constants preserve their source IEEE32 values exactly.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
from decode_bindpose_static_sections import decode_quat48, read_skeleton_reference

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
SOURCE=Path(r'D:/Unpack_3A/TLOU2/Assets/extracted_world_game_start/actor97/model-viewer.pak')
OUT=ROOT/'Exports/AnimationSources/DecodedOriginal'
REPORT=ROOT/'Content/TLOU2/Reports'


def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def align16(o): return (o+15)&~15


def package_resources(b):
    pages=[struct.unpack_from('<3I',b,u32(b,20)+12*i) for i in range(u32(b,16))]
    fixup=u32(b,28)
    owner,data,count=struct.unpack_from('<3I',b,fixup)
    fixups={}
    for i in range(count):
        source_page,target_page,relative=struct.unpack_from('<HHI',b,data+8*i)
        fixups[pages[source_page][0]+relative]=target_page
    def pointer(address,default_page):
        target_page=fixups.get(address,default_page)
        return pages[target_page][0]+u64(b,address)
    def cstr(address): return b[address:b.index(0,address)].decode('utf8')
    resources=[]
    for pi,(po,ps,flags) in enumerate(pages):
        if flags: continue
        for i in range(u16(b,po+18)):
            ro=u32(b,po+20+16*i+8);rs=po+ro
            resources.append(dict(page=pi,index=i,address=rs,
                name=cstr(pointer(rs,pi)),type=cstr(pointer(rs+8,pi))))
    return pages,resources,pointer


def main():
    b=SOURCE.read_bytes()
    pages,resources,pointer=package_resources(b)
    reference=read_skeleton_reference()
    palette=json.loads((REPORT/'SKELETON_CODEC_SECTION_PALETTES.json').read_text())
    nodes={r['bone_index']:r for r in palette['nodes']}
    all_outputs=[]
    for name in ['model-viewer-ellie-patrol','model-viewer-ellie-16-patrol','model-viewer-ellie','model-viewer-ellie-seattle']:
        r=next(r for r in resources if r['type']=='ANIM' and r['name']==name)
        address=pointer(r['address']+56,r['page'])
        size=u16(b,address+8)
        blob=b[address:address+size]
        checks={}
        def require(label,condition):
            checks[label]=bool(condition)
            if not condition: raise ValueError((name,label))
        require('codec_magic',u32(blob,0)==0x41430102)
        require('one_frame',u16(blob,14)==1)
        require('seven_sections',u16(blob,12)==7)
        tracks={};scalars=[];programs=[]
        # Section1 packs16 main-tail SQT records in the low byte and108
        # scalar parameters in the high byte. Together sections0/1 cover the
        # source hierarchy group0's143 SQT records exactly.
        bases=[0,127,322,360,456,555,649]
        counts=[127,16,38,96,99,94,50]
        for section in range(7):
            header=0x30+16*section
            start=u32(blob,header)
            count_word=u16(blob,header+6)
            count=count_word&255
            scalar_count=count_word>>8
            require('palette_count_'+str(section),count==counts[section])
            require('static_stride_'+str(section),u32(blob,header+12)==0)
            require('scalar_count_'+str(section),scalar_count==(108 if section==1 else 0))
            program=dict(section_index=section,offset=start,sqt_count=count,scalar_count=scalar_count,bone_base=bases[section],operations=[])
            pos=start
            for operation in range(32):
                op=u16(blob,pos)
                if op==0: break
                require('constant_opcode_'+str(pos),op in (0x315,0x316,0x318,0x319))
                padded,selector,relative=struct.unpack_from('<3H',blob,pos+2)
                require('table_selector_'+str(pos),selector==3)
                table=start+relative
                dests=list(struct.unpack_from('<'+'H'*padded,blob,table))
                sentinel=scalar_count*4 if op==0x319 else count*48
                active=[d for d in dests if d!=sentinel]
                require('sentinel_tail_'+str(pos),dests==active+[sentinel]*(padded-len(active)))
                data=align16(table+2*padded)
                width=12 if op==0x315 else 4 if op==0x319 else 6
                require('values_bounded_'+str(pos),data+width*len(active)<=len(blob))
                operation_info=dict(opcode=hex(op),offset=pos,table=table,data=data,padded_count=padded,active_count=len(active),destinations=dests)
                program['operations'].append(operation_info)
                for index,dest in enumerate(active):
                    src=data+width*index
                    if op==0x319:
                        require('scalar_destination_'+str(src),dest%4==0 and dest//4<scalar_count)
                        scalars.append(dict(section_index=section,parameter_index=dest//4,value=struct.unpack_from('<f',blob,src)[0],source_offset=src))
                        continue
                    local,slot=divmod(dest,48)
                    bi=bases[section]+local
                    require('sqt_destination_'+str(src),0<=local<count and bi in reference['transforms'])
                    t=tracks.setdefault(bi,dict(bone_index=bi,bone_name=nodes[bi]['bone_name'],parent_index=nodes[bi]['parent_index'],section_index=section,section_local_record=local,source_channels=[]))
                    if op in (0x315,0x316):
                        require('vector_component_'+str(src),slot in (0,32))
                        kind='scale' if slot==0 else 'translation'
                        value=list(struct.unpack_from('<3f' if op==0x315 else '<3e',blob,src))
                        require('unique_channel_'+str(src),kind not in t)
                        t[kind]=value
                    else:
                        require('rotation_component_'+str(src),slot==16)
                        kind='rotation'
                        value=decode_quat48(blob[src:src+6])['quaternion_xyzw']
                        require('unique_rotation_'+str(src),'rotations_xyzw' not in t)
                        t['rotations_xyzw']=[value]
                        t['rotation_channel']='constant_quat48'
                    t['source_channels'].append(dict(opcode=hex(op),payload_offset=src,destination=dest,kind=kind))
                pos+=8
            else: raise ValueError('unterminated program')
            program['terminator']=pos
            programs.append(program)
        ordered=[tracks[i] for i in sorted(tracks)]
        require('all520_original_sqt',set(tracks)==set(reference['transforms']))
        require('all108_scalars',len(scalars)==108 and len(set(r['parameter_index'] for r in scalars))==108)
        require('complete_sqt_tracks',all('scale' in t and 'translation' in t and 'rotations_xyzw' in t for t in ordered))
        require('finite_all_channels',all(math.isfinite(v) for t in ordered for values in [t['scale'],t['translation'],t['rotations_xyzw'][0]] for v in values))
        require('unit_quaternions',all(abs(sum(v*v for v in t['rotations_xyzw'][0])-1)<1e-6 for t in ordered))
        root=tracks[0]
        result=dict(schema='tlou2.original-local-sqt.v1',clip_name=name,source=dict(package=str(SOURCE),resource_absolute_offset=r['address'],resource_page=r['page'],codec_absolute_offset=address,codec_payload_bytes=size,codec_payload_sha256=hashlib.sha256(blob).hexdigest()),
            coordinates=dict(source_units='meters',up_axis='Y',space='local parent-relative S/Q/T',quaternion_order='xyzw',conversion_applied=False),
            frame_count=1,fps=30,sample_rate_hz=30,driven_bone_count=len(ordered),dynamic_bone_indices=[],tracks=ordered,scalar_parameters=scalars,operation_programs=programs,
            root_motion=dict(root_bone_index=0,root_driven_by_this_clip=True,trajectory_exported_from_this_clip=True,trajectory_is_static=True,source_translation=root['translation'],source_rotation_xyzw=root['rotations_xyzw'][0],policy='original one-frame catalog pose; zero displacement and no invented idle motion'),
            undriven_bone_policy=dict(all_node_count=1074,source_reference_sqt_count=520,undriven_node_count=554,policy='procedural/helper nodes retain explicit reference identity-local parent inheritance'),
            validation=dict(pass_=all(checks.values()),checks=checks),scope_note='Original gallery static pose. Procedural face/cloth constraints and capture-time simulation are not solved by this constant pose alone. Some source tongue/teeth translations are large and are retained exactly; native engine contextual solve may alter them.')
        result['validation']['pass']=result['validation'].pop('pass_')
        OUT.mkdir(parents=True,exist_ok=True)
        target=OUT/(name+'.json');target.write_text(json.dumps(result,indent=2))
        (OUT/(name+'.ndanim.bin')).write_bytes(blob)
        with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(['bone_index','bone_name','parent_index','section_index','sx','sy','sz','qx','qy','qz','qw','tx_m','ty_m','tz_m'])
            for t in ordered:w.writerow([t['bone_index'],t['bone_name'],t['parent_index'],t['section_index'],*t['scale'],*t['rotations_xyzw'][0],*t['translation']])
        all_outputs.append(dict(clip=name,path=str(target),source_offset=hex(address),payload_bytes=size,bones=len(ordered),scalars=len(scalars),checks=len(checks),pass_=all(checks.values()),root_translation=root['translation']))
    report=dict(source_package=str(SOURCE),package_sha256=hashlib.sha256(b).hexdigest(),archive='world-game-start.psarc',clips=all_outputs,pass_=all(r['pass_'] for r in all_outputs),section_palette_evidence='hierarchy group0 count143 = codec main127 + tail16; 16/108 share count_word0x6c10; remaining node-group counts38,96,99,94,50 match directly')
    (REPORT/'MODEL_VIEWER_STATIC_POSE_DECODE.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
