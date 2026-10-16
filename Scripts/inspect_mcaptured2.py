import unreal
for p in ['/Game/TLOU2/Materials/M_CapturedFrame','/Game/TLOU2/Materials/Exact/M_ND_jacket']:
 m=unreal.load_asset(p)
 try:
  ex=unreal.MaterialEditingLibrary.get_material_expressions(m); unreal.log('MEX '+p+' '+str(ex))
 except Exception as e: unreal.log_error('MEX ERR '+str(e))
