import pathlib,struct,json
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();D=json.loads(pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json').read_text());c=next(x for x in D['clips'] if x['anim_name']=='ellie-prone-lg-aim-strafe-0-fw');print(c)
for label,q in [('ANIM',c['anim_abs']),('RAW',c['raw_abs']),('CODEC',c['codec']['offset'])]:
 print('\n',label,hex(q))
 for o in range(q,q+0x180,16):print(f'{o-q:03x}: '+b[o:o+16].hex(' '))
