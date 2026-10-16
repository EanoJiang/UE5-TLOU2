import os,json,numpy as np
from pathlib import Path
root=Path('D:/TLOU2_UE5_8_Codex');ns={'__file__':str(root/'Scripts/decode_local_textures.py')};code=(root/'Scripts/decode_local_textures.py').read_text().split('records=[]')[0].replace('import bpy,','import ');exec(code,ns)
m=json.load(open(root/'Exports/TexturesDecoded/texture_decode_manifest.json'));r=next(x for x in m if x['name']=='ellie-head-normal.dds');d=r['dictionary_descriptor'];w=r['width'];h=r['height']
f=open(d['source_pak'],'rb');f.seek(d['payload_abs']);raw=f.read(w*h);import sys;sys.path.insert(0,str(root/'Scripts/vendor'));import texture2ddecoder as t
rgba=np.frombuffer(t.decode_bc7(raw,w,h),'u1').reshape(h,w,4)[:,:,[2,1,0,3]].copy();xy=rgba[:,:,:2].astype('f4')/127.5-1;z=np.sqrt(np.maximum(0,1-(xy*xy).sum(2)));rgba[:,:,2]=np.rint((z+1)*127.5).clip(0,255).astype('u1');ns['png'](str(root/'Exports/TexturesDecoded/ellie-head-normal-xyz.png'),w,h,rgba.tobytes())
