import pathlib,struct,json
for pak in [r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak',r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak']:
 b=pathlib.Path(pak).read_bytes();print('\n',pak)
 # use bind json or move json
 jp='D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/bindpose/codec_association_evidence.json' if 'bindpose' in pak else 'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json';D=json.loads(pathlib.Path(jp).read_text());
 for c in D['clips'][:4]:
  h=c['codec'];q=h['offset'];x=b[q:q+h['payload_size']]; print(c['anim_name'],h['payload_size'],h['groups'],h['frames']);
  print('u16 0x30-0x50',[hex(v) for v in struct.unpack_from('<16H',x,0x30)])
