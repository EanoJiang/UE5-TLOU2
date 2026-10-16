import json,numpy as np
from pathlib import Path
r=Path('D:/TLOU2_UE5_8_Codex/Exports/ExactDebug')
for f in ['keyart_turntable_wet_large','keyart_turntable_concrete_large','keyart_turntable_fg']:
 d=json.load(open(r/f/'capture.json'))
 for m in d['meshes']:
  if f.endswith('fg') and 'fern' not in m['material']:continue
  if f.endswith('concrete_large') and 'moss' not in m['material']:continue
  z=np.load(r/f/m['npz']);p=np.frombuffer(z['pos_raw'].tobytes(),'<f4');n=m['vertex_count'];p=p[:n*4].reshape(n,4)[:,:3] if len(p)>=n*4 else p[:n*3].reshape(n,3)
  print(f,m['name'],m['material'],p.min(0).round(3),p.max(0).round(3))
