import unreal
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact',recursive=True):
 m=unreal.load_asset(p)
 if isinstance(m,unreal.Material):
  ex=m.get_editor_property('expressions'); vals=[]
  for e in ex:
   if isinstance(e,unreal.MaterialExpressionTextureSampleParameter2D):
    vals.append((str(e.get_editor_property('parameter_name')),str(e.get_editor_property('texture'))))
  unreal.log('MAT '+p+' '+str(vals))
