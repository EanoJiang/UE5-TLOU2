import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak';b=open(p,'rb').read();
for o in [35144,35208,35256,35360,35464,35568,35672,35776,35880,36064]:
 print('\nOFFSET',o,'hex',b[o:o+256].hex(' '))
 for i in range(0, min(256,len(b)-o),8):
  q=struct.unpack_from('<Q',b,o+i)[0]; print(f'{i:3} {q:016x}',end='; ')
  if i%32==24:print()
 print()
