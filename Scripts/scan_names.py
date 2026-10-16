import re,os
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\ellie-skel.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak']:
 b=open(p,'rb').read(); print(os.path.basename(p),len(b))
 for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_\-]{2,}\x00',b):
  s=m.group()[:-1]
  if any(x in s.lower() for x in [b'root',b'spine',b'head',b'anim',b'bind',b'ellie']): print(hex(m.start()),s)
