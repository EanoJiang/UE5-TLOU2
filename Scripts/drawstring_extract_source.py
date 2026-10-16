"""Extract the omitted strings without running the canonical extraction batch."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
OUT = ROOT/'Exports/Drawstring'
SOURCE = Path('D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/ellie-patrol-hoodie-string-cloth.pak')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    original = (ROOT/'Scripts/extract_nd_pak_fake.py').read_text()
    marker = "\nroot=r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97'"
    prelude,tail = original.split(marker,1)
    ns = {'__name__':'drawstring_compat'}
    exec(compile(prelude,str(ROOT/'Scripts/extract_nd_pak_fake.py'),'exec'),ns)
    ns['ns']['dialogOptions'].doLODs = True
    ns['INPUT_NAME'] = str(SOURCE)
    ns['OUTPUT_NAME'] = str(OUT/'capture.json')
    cap = ns['cap']
    pak = ns['PakFile'](ns['NoeBitStream'](SOURCE.read_bytes()),{'path':str(SOURCE)})
    pak.readPakHeader()
    pak.readPak()
    pak.loadGeometry()
    meshes=[]
    for i,mesh in enumerate(cap.meshes):
        arrays={'indices_raw':np.frombuffer(mesh['indices'],dtype=np.uint8)}
        binds={}
        for key,(raw,typ,stride,*extra) in mesh['binds'].items():
            arrays[key+'_raw']=np.frombuffer(raw,dtype=np.uint8)
            binds[key]={'type':int(typ),'stride':int(stride),'extra':list(extra)}
        filename='mesh_%04d.npz'%i
        np.savez_compressed(OUT/filename,**arrays)
        meshes.append(dict(name=mesh['name'],material=mesh['material'],count=mesh['count'],
            vertex_count=mesh['vertex_count'],index_type=mesh['index_type'],npz=filename,bindings=binds))
    doc=dict(source='ellie_patrol_hoodie_string_cloth',pak=SOURCE.name,
        source_package=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        meshCount=len(meshes),meshes=meshes,parser='canonical compatibility prelude, batch excluded',
        boneCount=len(pak.boneList or []))
    (OUT/'capture.json').write_text(json.dumps(doc,indent=2))
    # Use original SQT decoder without its write-producing main function.
    sys.path.insert(0,str(ROOT/'Scripts'))
    from export_owned_clothing_skeletons import decode_owned
    rig=decode_owned(SOURCE.name)
    (OUT/'owned_rig22.json').write_text(json.dumps(rig,indent=2))
    print('DRAWSTRING_EXTRACT '+json.dumps(dict(meshes=meshes,bones=rig['bone_count'])))

if __name__ == '__main__': main()
