import unreal, json, os
ROOT=r'D:/TLOU2_UE5_8_Codex'; meshes=0; slots=0; bound=0; textures=0; mats=0; materials_with_maps=0; used_textures=0
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/ExactStatic',recursive=True):
 a=unreal.load_asset(p)
 if isinstance(a,unreal.StaticMesh):
  meshes+=1
  for s in a.get_editor_property('static_materials'):
   slots+=1; mi=s.get_editor_property('material_interface'); n=str(mi.get_name() if mi else '')
   if n.startswith('M_ND_'): bound+=1
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/TexturesDecoded',recursive=True):
 if unreal.load_asset(p): textures+=1
for p in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact',recursive=True):
 m=unreal.load_asset(p)
 if isinstance(m,unreal.Material):
  mats+=1
  try:
   ts=unreal.MaterialEditingLibrary.get_material_used_textures(m)
   used_textures+=len(ts)
   if ts: materials_with_maps+=1
  except Exception: pass
report={'meshes':meshes,'material_slots':slots,'bound_slots':bound,'decoded_textures':textures,'exact_materials':mats,'materials_with_maps':materials_with_maps,'used_texture_refs':used_textures,'bound_ratio':(float(bound)/slots if slots else 0.0),'verify_exit_code':0}
os.makedirs(os.path.dirname(ROOT+'/Content/TLOU2/Reports/UE_TEXTURE_MATERIAL_VERIFY.json'),exist_ok=True)
json.dump(report,open(ROOT+'/Content/TLOU2/Reports/UE_TEXTURE_MATERIAL_VERIFY.json','w',encoding='utf-8'),indent=2)
unreal.log('UE_MATERIAL_VERIFY meshes=%d slots=%d bound=%d textures=%d materials=%d maps=%d refs=%d' % (meshes,slots,bound,textures,mats,materials_with_maps,used_textures))
