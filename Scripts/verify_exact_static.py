import unreal
assets=unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/ExactStatic',recursive=True)
meshes=[]
for p in assets:
    a=unreal.load_asset(p)
    if isinstance(a,unreal.StaticMesh): meshes.append(a)
lvl=unreal.load_asset('/Game/TLOU2/Maps/ElliePatrolCatalog')
unreal.log('VERIFY_EXACT_STATIC count=%d level=%s' % (len(meshes),str(lvl)))
