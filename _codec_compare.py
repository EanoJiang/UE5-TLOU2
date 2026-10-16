import struct,json,pathlib,hashlib
p=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak'); b=p.read_bytes();
po=9541328 # page9
# exact clips parser from JSON
D=json.loads(pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json').read_text())
for name in ['ellie-prone-lg-aim-strafe-0-fw','ellie-prone-lg-aim-strafe-0-fw-crossbow','ellie-prone-lg-aim-strafe-90r-fw','ellie-prone-lg-aim-strafe-90r-fw-crossbow','ellie-prone-lg-aim-strafe-180-fw','ellie-prone-lg-aim-strafe-180-fw-crossbow']:
 c=[x for x in D['clips'] if x['anim_name']==name][0]; q=c['codec']['offset'];
 h=b[q:q+c['codec']['payload_size']]; print('\n',name,'page',c['page'],'anim',c['anim_entry'],'codec',hex(q), 'payload',len(h),'sha',hashlib.sha1(h).hexdigest());
 # bytes +0x00..+0x60 words
 for off in range(0,0xA0,0x10): print(f'{off:03x}:',h[off:off+16].hex(' '))
 print('u16@120', [hex(x) for x in struct.unpack_from('<16H',h,0x120)]);
 print('u16@160', [hex(x) for x in struct.unpack_from('<16H',h,0x160)]);
 print('u16@2d0', [hex(x) for x in struct.unpack_from('<40H',h,0x2d0)]);
 print('u16@410', [hex(x) for x in struct.unpack_from('<24H',h,0x410)]);
 print('last',h[0x9b0:0x9b0+16].hex(' '))
