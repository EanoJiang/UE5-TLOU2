import pathlib,json,struct
D=json.loads(pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/bindpose/codec_association_evidence.json').read_text()); b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak').read_bytes();
for c in D['clips']:
 print('\n',c['page'],c['anim_entry'],c['anim_name'],'raw',c['raw_entry'],c['raw_count'],'codec',c['codec']);
 if c['codec']:
  h=c['codec'];x=b[h['offset']:h['offset']+h['payload_size']]; print('bytes',len(x),'head',x[:0xa0].hex(' '));
  for o in [0x50,0x120,0x160,0x2d0,0x410]:
   if o<len(x):print(hex(o),[hex(v) for v in struct.unpack_from('<'+str(min(16,(len(x)-o)//2))+'H',x,o)])
