import unreal
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/ExactStatic',recursive=True):
 a=unreal.load_asset(p)
 if isinstance(a,unreal.StaticMesh):
  vals=[]
  for x in a.get_editor_property('static_materials'):
   vals.append((str(x.get_editor_property('material_slot_name')),str(x.get_editor_property('material_interface'))))
  unreal.log('SLOT '+p+' '+str(vals))
