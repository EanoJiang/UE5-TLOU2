import unreal
for p in ['/Game/TLOU2/Materials/M_CapturedFrame']:
 m=unreal.load_asset(p); unreal.log('MC '+str(unreal.MaterialEditingLibrary.get_num_material_expressions(m))+' '+str(unreal.MaterialEditingLibrary.get_material_used_textures(m)))
