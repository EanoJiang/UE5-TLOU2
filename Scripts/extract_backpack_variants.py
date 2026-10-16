"""Compare character-bound backpack variants without replacing existing files."""
from pathlib import Path

bootstrap=Path(r'D:/TLOU2_UE5_8_Codex/Scripts/extract_nd_pak_fake.py').read_text()
exec(compile(bootstrap.split('for fname in packages:')[0],'<Noesis compatibility bootstrap>','exec'),globals())

outroot=r'D:/TLOU2_UE5_8_Codex/Exports/BackpackVariantDebug'
os.makedirs(outroot,exist_ok=True)
skelpath=os.path.join(root,'ellie-skel.pak')
skel=PakFile(NoeBitStream(open(skelpath,'rb').read()),{'path':skelpath})
skel.readPakHeader();skel.readPak()
for fname in ['ellie16-backpack.pak','ellie-backpack.pak','backpack-ellie-16.pak']:
    path=os.path.join(root,fname)
    INPUT_NAME=path;OUTPUT_NAME=os.path.join(outroot,fname+'.json')
    ns['INPUT_NAME']=INPUT_NAME;ns['OUTPUT_NAME']=OUTPUT_NAME
    cap.meshes=[];cap.current={}
    pak=PakFile(NoeBitStream(open(path,'rb').read()),{'path':path})
    pak.readPakHeader();pak.readPak()
    if not pak.jointOffset:
        pak.boneList=skel.boneList;pak.boneMap=skel.boneMap;pak.boneDict=skel.boneDict
    # PC backpack meshes mix packed22/10 records and float32/u32 pairs.
    # The original per-mesh skin header at mapOffsetAddr-16 identifies these:
    # uknSD2=1 means float32 weight + uint32 joint, 0 means packed22/10.
    # The legacy plugin only honors that flag in TLOUP1 mode.
    skin_format_headers=[]
    if fname in ['ellie16-backpack.pak','ellie-backpack.pak']:
        for submesh in pak.submeshes:
            if submesh.skinDesc:
                header=struct.unpack_from('<4I',pak.bs.buf,submesh.skinDesc.mapOffsetAddr-16)
                submesh.skinDesc=submesh.skinDesc._replace(uncompressed=bool(header[2]))
                skin_format_headers.append(dict(name=submesh.name,vertices=submesh.numVerts,header=list(header),
                    source_format='float32_weight_uint32_joint' if header[2] else 'packed22_weight_10_joint'))
    pak.loadGeometry()
    export_capture(pak,Path(fname).stem.replace('-','_'))
    export_texture_headers(pak,Path(fname).stem.replace('-','_'))
    Path(outroot,Path(fname).stem.replace('-','_'),'skin_format_headers.json').write_text(json.dumps(skin_format_headers,indent=2))
    skin_sources=[]
    for submesh in pak.submeshes:
        if not submesh.skinDesc:
            continue
        maps=bytes(pak.bs.buf[submesh.skinDesc.mapOffset:submesh.skinDesc.mapOffset+8*submesh.numVerts])
        records=[struct.unpack_from('<2I',maps,8*i) for i in range(submesh.numVerts)]
        zeros=[i for i,v in enumerate(records) if v[0]==0]
        skin_sources.append(dict(name=submesh.name,vertices=submesh.numVerts,skin_descriptor=dict(submesh.skinDesc._asdict()),
            source_zero_influence_vertices=zeros,first_zero_records=[dict(vertex=i,record=records[i])for i in zeros[:10]],
            influence_count_histogram={str(n):sum(v[0]==n for v in records)for n in sorted(set(v[0]for v in records))}))
    Path(outroot,Path(fname).stem.replace('-','_'),'skin_source_descriptors.json').write_text(json.dumps(skin_sources,indent=2))
    print('BACKPACK_VARIANT',fname,[(m['name'],m['vertex_count'],m['material'])for m in cap.meshes])
