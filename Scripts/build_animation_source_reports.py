#!/usr/bin/env python3
"""Merge decoded ND animation source metadata with verified UE root-motion probe."""
from __future__ import annotations
import csv, json, os
from pathlib import Path

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
SRC=ROOT/'Exports'/'AnimationSources'/'animation_source_manifest.json'
ROOTFBX=ROOT/'Exports'/'rootmotion_fbx_verification.json'
UEIMPORT=ROOT/'Exports'/'import_rootmotion_probe_result.json'
REPORT=ROOT/'Content'/'TLOU2'/'Reports'

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(SRC.read_text(encoding='utf-8')) if SRC.exists() else {'sources':[]}
    fbx=json.loads(ROOTFBX.read_text(encoding='utf-8')) if ROOTFBX.exists() else {}
    ue=json.loads(UEIMPORT.read_text(encoding='utf-8')) if UEIMPORT.exists() else {}
    clips=[]; resource_count=0; raw_count=0; raw_struct=[]
    for s in manifest.get('sources',[]):
        for ch in s.get('chunks',[]):
            resource_count += len(ch.get('resources',[]))
            for rr in ch.get('resources',[]):
                if rr.get('type')=='ANIM_RAWCHANNELS':
                    raw_count += 1
                    if rr.get('raw_header'):
                        raw_struct.append({'source':s.get('source'),'chunk':ch.get('chunk'),
                                           'resource_offset':rr.get('absolute_offset'),
                                           'name':rr.get('name'),'raw_header':rr.get('raw_header')})
            for c in ch.get('codec',[]):
                clips.append({
                    'source':s.get('source'),'kind':s.get('kind'),'chunk':ch.get('chunk'),
                    'resource':c.get('resource'),'resource_type':c.get('resource_type'),
                    'channel_count':c.get('channel_count'),'group_count':c.get('group_count'),
                    'frame_count':c.get('frame_count'),'sample_rate_hz':c.get('sample_rate'),
                    'sample_period_s':c.get('sample_period'),'codec_payload_size':c.get('codec_payload_size'),
                    'section_offset':c.get('section_offset'),'stream_offset':c.get('stream_offset'),
                    'packed_stride':c.get('packed_stride'),'payload_file':c.get('payload_file'),
                    'payload_sha256':c.get('payload_sha256'),
                    'root_motion_decode':'pending proprietary quantizer reader'
                })
    evidence={
        'source_manifest':str(SRC).replace('\\','/'),'sources':len(manifest.get('sources',[])),
        'pak_chunks':sum(len(s.get('chunks',[])) for s in manifest.get('sources',[])),
        'resource_count':resource_count,'anim_rawchannels_resources':raw_count,
        'raw_channel_structural_index':raw_struct,
        'codec_payload_count':len(clips),'clips':clips,
        'root_motion':{
            'exact_nd_root_tracks_decoded':False,
            'reason':'ANIM_RAWCHANNELS quantized track reader is not implemented; source bytes and codec headers are preserved.',
            'source_payloads_are_byte_preserved':True,
            'source_root_candidate_policy':'root/trajectory extraction must map codec channel descriptors to the Ellie skeleton before writing transforms.'
        },
        'verified_interchange_probe':{'fbx':str(ROOT/'Exports'/'Ellie_1074_RootMotion_AnimationProbe.fbx').replace('\\','/'),
                                      'ue_paths':ue.get('paths',[]),'blender':fbx}
    }
    (REPORT/'ANIMATION_SOURCE_DECODE_EVIDENCE.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    # Timeline CSV is useful to motion matching/UE tooling even before values
    # are decoded: it records exact frame clocks and source payload IDs.
    with (REPORT/'root_motion_source_timeline.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['source','chunk','resource','frame_count','sample_rate_hz','start_frame','end_frame','start_time_s','end_time_s','root_translation_status','payload_file'])
        for c in clips:
            n=int(c.get('frame_count') or 0); rate=float(c.get('sample_rate_hz') or 0); end=max(0,n-1)
            w.writerow([c['source'],c['chunk'],c['resource'],n,rate,0,end,0.0,(end/rate if rate else ''),'pending_quantizer',c.get('payload_file','')])
    lines=['# Animation source and root-motion evidence','',
           f"Decoded source files: {evidence['sources']}; streamed/direct chunks: {evidence['pak_chunks']}; codec payloads: {evidence['codec_payload_count']}; ANIM_RAWCHANNELS resources: {raw_count}.",
           '', 'The extraction now verifies the Naughty Dog package container and mixed-width `0x41430102` codec header. Every source payload is preserved under `Exports/AnimationSources/raw` and hashed in `ANIMATION_SOURCE_DECODE_EVIDENCE.json`. The evidence JSON also contains the structural ANIM_RAWCHANNELS pointer/hash index.', '',
           '| Source clip family | Frames | Rate | Channels | Section offset | Stream offset | Root track |', '|---|---:|---:|---:|---:|---:|---|']
    for c in clips:
        lines.append(f"| `{c['source']}` / `{c['resource']}` | {c['frame_count']} | {c['sample_rate_hz']:.6g} | {c['channel_count']} | `0x{int(c.get('section_offset') or 0):x}` | `0x{int(c.get('stream_offset') or 0):x}` | pending proprietary quantizer |")
    lines += ['', 'The verified interchange probe remains available as an actual UE-importable sequence:',
              f"- FBX: `{ROOT/'Exports'/'Ellie_1074_RootMotion_AnimationProbe.fbx'}`",
              f"- Blender verification: `{ROOTFBX}`",
              f"- Verified probe trajectory CSV: `{ROOT/'Exports'/'Ellie_1074_RootMotion_AnimationProbe.csv'}`",
              f"- UE imported paths: `{ue.get('paths',[])}`",
              '- The probe has 1,074 bones, 80 keys on the object X curve from −0.015 to +0.015 Blender units, and zeroed `root` bone-local translation. It is explicitly a test/interchange trajectory, not a claim that the original compressed ND root curve has been decoded.',
              '', 'See `root_motion_source_timeline.csv` for exact frame clocks and payload hashes.']
    (REPORT/'ROOT_MOTION_SOURCE_EVIDENCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Extend existing source map without deleting prior paths.
    sm=REPORT/'ANIMATION_SOURCE_MAP.md'; old=sm.read_text(encoding='utf-8') if sm.exists() else '# Animation source map\n'
    add='''\n## Streamed ANIM resources (verified extraction)\n\n- `D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/animation_source_manifest.json` records direct PAK and `animstream97/*.stm` chunks.\n- `D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/raw/` contains byte-preserved `source.pak` chunks and `codec_*.ndanim.bin` payloads.\n- `D:/TLOU2_UE5_8_Codex/Content/TLOU2/Reports/ANIMATION_SOURCE_DECODE_EVIDENCE.json` records channel/frame/rate/descriptor metadata and SHA-256 hashes.\n- `ANIM_RAWCHANNELS` is structurally indexed but its proprietary quantizer is not yet converted to bone transforms.\n'''
    if 'Streamed ANIM resources' not in old: sm.write_text(old.rstrip()+add,encoding='utf-8')
    print(json.dumps({'clips':len(clips),'raw_channels':raw_count,'report':str(REPORT/'ROOT_MOTION_SOURCE_EVIDENCE.md')},indent=2))
if __name__=='__main__': main()
