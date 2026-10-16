import json,pathlib,struct
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();D=json.loads(pathlib.Path(r'D:/TLOU2_UE5_8_Codex/Exports/AnimationSources/DecodedRawChannels/move2/codec_association_evidence.json').read_text());
seen=[]
for c in D['clips']:
 h=c['codec']
 if not h:continue
 if h['groups'] in [1,2,3,4,5,6,7] and c['anim_name'] not in [x[0] for x in seen]:seen.append((c['anim_name'],h['groups'],h['frames'],h['payload_size'],h['offset'],c['page']))
# selected first groups each
for name,g,fr,sz,q,page in seen:
 if g<=2 or name.startswith('ellie-prone-lg'):
  h=b[q:q+sz]; print('\n',name,'g',g,'fr',fr,'size',sz,'q',hex(q));
  for o in range(0x0, min(0x500,sz),0x10):
   if o>=0x100 and o<0x180 or o<0x80: print(f'{o:03x}: '+h[o:o+16].hex(' '))
  print('120-200');
  for o in range(0x120,min(0x220,sz),0x10):print(f'{o:03x}: '+h[o:o+16].hex(' '))
  if g<=2: break
