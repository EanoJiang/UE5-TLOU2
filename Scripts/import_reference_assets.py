import unreal, os
root=r"D:/TLOU2_UE5_8_Codex"
png=root+"/Content/TLOU2/Reference/captured_frame.png"
at=unreal.AssetToolsHelpers.get_asset_tools()
task=unreal.AssetImportTask(); task.filename=png; task.destination_path='/Game/TLOU2/Reference'; task.destination_name='T_CapturedFrame'; task.automated=True; task.replace_existing=True; task.save=True
at.import_asset_tasks([task])
tex=unreal.load_asset('/Game/TLOU2/Reference/T_CapturedFrame')
unreal.log('IMPORTED '+str(tex))
mat_path='/Game/TLOU2/Materials/M_CapturedFrame'; mat=unreal.load_asset(mat_path)
if not mat:
    mat=at.create_asset('M_CapturedFrame','/Game/TLOU2/Materials',unreal.Material,unreal.MaterialFactoryNew())
if mat and tex:
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    s=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,-500,0)
    s.set_editor_property('parameter_name','CapturedFrame'); s.set_editor_property('texture',tex)
    unreal.MaterialEditingLibrary.connect_material_property(s,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(s,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('MATERIAL '+str(mat))
unreal.log('DONE_REFERENCE_ASSETS')

