import struct
files=[r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak',r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak']
target=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
for p in files:
 b=open(p,'rb').read(); print('\n',p,len(b))
 for x in target:
  bb=struct.pack('<Q',x); hits=[];o=0
  while 1:
   q=b.find(bb,o)
   if q<0:break
   hits.append(q);o=q+1
  print(hex(x),hits[:50], 'count',len(hits))
