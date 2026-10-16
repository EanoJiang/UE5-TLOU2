import pathlib,struct,json
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-bindpose.pak').read_bytes();D=json.loads(pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/bindpose/codec_association_evidence.json').read_text())
for name in ['bindpose-add','bindpose-anim','bindpose-null-add','bindpose-null-backpack']:
 c=next(x for x in D['clips'] if x['anim_name']==name);h=c['codec'];q=h['offset'];x=b[q:q+h['payload_size']];print('\n',name,'size',len(x),'stream',hex(struct.unpack_from('<I',x,0x38)[0]),'end',hex(struct.unpack_from('<I',x,0x48)[0]))
 for o in range(0x110,min(struct.unpack_from('<I',x,0x38)[0],len(x)),16): print(f'{o:03x}: '+x[o:o+16].hex(' '))
