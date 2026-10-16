"""Soften the overly broad white highlights observed in the first RHI preview."""
import json
from pathlib import Path
import unreal

path = '/Game/TLOU2/Groom/M_Ellie_CaptureGroom_Hair'
material = unreal.load_asset(path)
assert isinstance(material, unreal.Material), path
values = ((unreal.MaterialProperty.MP_ROUGHNESS, .62),
          (unreal.MaterialProperty.MP_SPECULAR, .25))
for prop, value in values:
    node = unreal.MaterialEditingLibrary.get_material_property_input_node(material, prop)
    assert isinstance(node, unreal.MaterialExpressionConstant), (prop, node)
    node.set_editor_property('r', value)
unreal.MaterialEditingLibrary.recompile_material(material)
assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
report = {'material': material.get_path_name(), 'roughness': .62, 'specular': .25,
          'reason': 'First actual RHI close-up showed broad white crown reflections; retain dark-brown pigment and soften the strand specular response.'}
Path('D:/TLOU2_UE5_8_Codex/Exports/Groom/material_calibration.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('GROOM_MATERIAL_CALIBRATION ' + json.dumps(report))
