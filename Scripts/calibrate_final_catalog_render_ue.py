import unreal
import json
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
exec(compile((ROOT/'Scripts/fix_final_material_skeletal_morph_usage_ue.py').read_text(),'fix_final_material_skeletal_morph_usage_ue.py','exec'),{'__name__':'__main__'})
unreal.EditorLevelLibrary.load_level('/Game/TLOU2/Maps/ElliePatrolCaptureMatched')
actors=unreal.EditorLevelLibrary.get_all_level_actors()
for actor in actors:
    if isinstance(actor,unreal.SkeletalMeshActor):
        actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=4.8182263022,roll=0),False)
    if isinstance(actor,unreal.PostProcessVolume):
        settings=actor.get_editor_property('settings')
        settings.set_editor_property('override_auto_exposure_bias',True)
        settings.set_editor_property('auto_exposure_bias',-9.0)
        actor.set_editor_property('settings',settings)
changed=[]
for path in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/Materials/Exact',recursive=True):
    mat=unreal.load_asset(path)
    if not isinstance(mat,unreal.Material) or not mat.get_name().startswith('M_ND_hair'): continue
    if unreal.EditorAssetLibrary.get_metadata_tag(mat,'CatalogHairLinearTint')=='0.35': continue
    source=unreal.MaterialEditingLibrary.get_material_property_input_node(mat,unreal.MaterialProperty.MP_BASE_COLOR)
    if not source: continue
    multiply=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionMultiply,-200,-200)
    multiply.set_editor_property('const_b',.35)
    multiply.set_editor_property('desc','Catalog hair brightness reconstruction; original anisotropic shader is preserved separately.')
    unreal.MaterialEditingLibrary.connect_material_expressions(source,'',multiply,'A')
    unreal.MaterialEditingLibrary.connect_material_property(multiply,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.EditorAssetLibrary.set_metadata_tag(mat,'CatalogHairLinearTint','0.35')
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    changed.append(mat.get_path_name())
unreal.EditorLevelLibrary.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(ROOT/'Exports/catalog_render_calibration.json').write_text(json.dumps({'manual_exposure_bias':-9.0,'actor_yaw_degrees':4.8182263022,
    'hair_materials_changed':changed,'hair_linear_basecolor_tint':.35,
    'status':'Rendering calibration against reference; exact skin/camera matrices preserved.'},indent=2))
