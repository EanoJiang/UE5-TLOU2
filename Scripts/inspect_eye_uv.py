import json,numpy as np
p='D:/TLOU2_UE5_8_Codex/Exports/ExactDebug/ellie_head';d=json.load(open(p+'/capture.json'))
for m in d['meshes']:
 if m['material']=='eyes':
  z=np.load(p+'/'+m['npz']);
  for k in ['uv0','uv1']:
   u=np.frombuffer(z[k+'_raw'].tobytes(),'<f4').reshape(-1,2);print(k,u.min(0),u.max(0),u[:10])
