"""Losslessly provide JSON glTF+BIN alongside the canonical binary glTFs."""
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
stems=['Ellie_Patrol_Catalog_CaptureMatched','Ellie_Patrol_CapturedSkinPose',
       'Ellie16_Patrol_OriginalViewerPose','Ellie_Patrol_Original_0FW']
rows=[]
for stem in stems:
    path=ROOT/'Exports'/(stem+'.glb')
    blob=path.read_bytes()
    magic,version,length=struct.unpack_from('<4sII',blob)
    assert magic==b'glTF' and version==2 and length==len(blob)
    offset=12
    chunks={}
    while offset<len(blob):
        size,kind=struct.unpack_from('<II',blob,offset)
        chunks[kind]=blob[offset+8:offset+8+size]
        offset+=8+size
    original=json.loads(chunks[0x4e4f534a])
    assert len(original['buffers'])==1 and 'uri' not in original['buffers'][0]
    doc=json.loads(json.dumps(original))
    doc['buffers'][0]['uri']=stem+'.bin'
    binary=chunks[0x004e4942][:doc['buffers'][0]['byteLength']]
    (ROOT/'Exports'/(stem+'.bin')).write_bytes(binary)
    (ROOT/'Exports'/(stem+'.gltf')).write_text(json.dumps(doc,indent=2),encoding='utf-8')
    restored=json.loads((ROOT/'Exports'/(stem+'.gltf')).read_text())
    restored['buffers'][0].pop('uri')
    assert restored==original and (ROOT/'Exports'/(stem+'.bin')).read_bytes()==binary
    rows.append({'source_glb':str(path),'source_sha256':hashlib.sha256(blob).hexdigest(),
                 'gltf':str(ROOT/'Exports'/(stem+'.gltf')),'bin':str(ROOT/'Exports'/(stem+'.bin')),
                 'logical_binary_bytes':len(binary),'json_semantically_identical':True,'binary_identical':True})
out={'pass':True,'rows':rows,'images_note':'Images remain embedded buffer views in the BIN; both files travel together.'}
(ROOT/'Exports/canonical_gltf_split_validation.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'pass':True,'files':len(rows)*2}))
