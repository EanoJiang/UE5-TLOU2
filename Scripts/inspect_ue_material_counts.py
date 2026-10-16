import unreal
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact',recursive=True):
 m=unreal.load_asset(p)
 if isinstance(m,unreal.Material):
  unreal.log('MATCOUNT '+p+' '+str(unreal.MaterialEditingLibrary.get_num_material_expressions(m))+' '+str(unreal.MaterialEditingLibrary.get_material_used_textures(m)))
