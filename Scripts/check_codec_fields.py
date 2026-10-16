import json,glob,struct
for p in glob.glob(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\\*\\source.pak'):
 b=open(p,'rb').read(); hits=[i for i in range(len(b)) if b.startswith(b'\x02\x01CA',i)]
 if hits: print('\n',p,len(b),hits)
 for h in hits[:3]:
  print('u16', [struct.unpack_from('<H',b,h+o)[0] for o in range(0,52,2)])
  print('u32', [struct.unpack_from('<I',b,h+o)[0] for o in range(0,52,4)])
