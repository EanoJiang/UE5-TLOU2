import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
path=ROOT+'/Scripts/import_decoded_materials_ue.py'
ns={'__name__':'eye_material'}
exec(compile(open(path).read().split('textures = import_textures()')[0],path,'exec'),ns)
textures={}
for stem in ['ellie-eyes-reconstructed-basecolor','ellie-eyes-reconstructed-normal']:
    task=unreal.AssetImportTask();task.filename=ROOT+'/Exports/TexturesDecoded/'+stem+'.png';task.destination_path='/Game/TLOU2/TexturesDecoded';task.destination_name=stem;task.automated=True;task.replace_existing=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    textures[stem]=unreal.load_asset(task.imported_object_paths[0])
ns['COLOR']['eyes']='ellie-eyes-reconstructed-basecolor'
ns['NORMAL']['eyes']='ellie-eyes-reconstructed-normal'
ns['AO'].pop('eyes',None)
mat=ns['make_material']('eyes',textures)
# Portable eye surface response. Corneal optics remain explicitly unported.
rough=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-250,850)
rough.set_editor_property('r',.18)
unreal.MaterialEditingLibrary.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('RECONSTRUCTED_EYE_MATERIAL '+mat.get_path_name())
for stem in ['ellie-caruncle-color','ellie-caruncle-normal','tear-normal','tear-mask']:
    textures[stem]=unreal.load_asset('/Game/TLOU2/TexturesDecoded/'+stem)
ns['COLOR']['tearduct']='ellie-caruncle-color'
ns['NORMAL']['tearduct']='ellie-caruncle-normal'
tearduct=ns['make_material']('tearduct',textures)
ns['NORMAL']['tears']='tear-normal'
tears=ns['make_material']('tears',textures)
tears.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
tears.set_editor_property('two_sided',True)
opacity=unreal.MaterialEditingLibrary.create_material_expression(tears,unreal.MaterialExpressionConstant,-250,850)
opacity.set_editor_property('r',.08)
unreal.MaterialEditingLibrary.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
rough=unreal.MaterialEditingLibrary.create_material_expression(tears,unreal.MaterialExpressionConstant,-250,950)
rough.set_editor_property('r',.12)
unreal.MaterialEditingLibrary.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
unreal.MaterialEditingLibrary.recompile_material(tears)
unreal.EditorAssetLibrary.save_loaded_asset(tears)
