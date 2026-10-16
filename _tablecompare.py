import pathlib,struct,json,collections
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();D=json.loads(pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json').read_text())
for name in ['ellie-prone-lg-aim-strafe-0-fw','ellie-prone-lg-aim-strafe-90r-fw','ellie-prone-lg-aim-strafe-0-l','ellie-prone-lg-aim-strafe-90r-r','ellie-prone-lg-aim-strafe-180-fw','ellie-prone-move-fw-b','ellie-death-fire-90r']:
 c=next(x for x in D['clips'] if x['anim_name']==name); h=c['codec']; q=h['offset']; x=b[q:q+h['payload_size']]; print('\n',name,'fr',h['frames'],'size',len(x),'header offs')
 print('u32',[(hex(o),hex(struct.unpack_from('<I',x,o)[0])) for o in range(0x30,0x50,4)])
 # print u16 tables around +0x160, +0x2d0,+0x410 limited
 for base, count in [(0x120,16),(0x160,16),(0x2d0,40),(0x410,24)]:
  if base+count*2<=len(x):
   vals=struct.unpack_from('<'+str(count)+'H',x,base); print(hex(base),len(vals),[hex(v) for v in vals])
