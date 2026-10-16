import os,struct,json,sys,numpy as np
code=open('Scripts/decode_local_textures.py').read().split('records=[]')[0].replace('import bpy,','import ')
ns={'__file__':os.path.abspath('Scripts/decode_local_textures.py')};exec(code,ns)
os.makedirs('Exports/TextureDiagnostic',exist_ok=True)
manifest=json.load(open('Exports/TexturesDecoded/texture_decode_manifest.json'))
for name in ['ellie-head-color.dds','ellie-patrol-jacket-color.dds','ellie-patrol-pants-color.dds']:
 r=next(x for x in manifest if x['name']==name); f=open('D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/'+r['source_pak'],'rb');f.seek(r['payload_abs']);raw=f.read(r['size']);w=r['width'];h=r['height'];bs=8;bw=(w+3)//4;bh=(h+3)//4
 for pitch in [bw*bs,256,512]:
  data=b''.join(raw[y*pitch:y*pitch+bw*bs] for y in range(bh));rgba=ns['decode'](data,w,h,r['format_name']);out='Exports/TextureDiagnostic/'+name[:-4]+'_pitch'+str(pitch)+'.png';ns['png'](out,w,h,rgba);print(out)
