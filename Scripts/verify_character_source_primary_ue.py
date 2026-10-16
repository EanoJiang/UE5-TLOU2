"""Read-only fresh-editor persistence verification of character primary graphs."""
import json
from pathlib import Path
import unreal
ROOT = Path('D:/TLOU2_UE5_8_Codex')
manifest = json.loads((ROOT / 'Exports/source_character_material_manifest.json').read_text())
mel = unreal.MaterialEditingLibrary
rows = []
for name, spec in manifest['materials'].items():
    mat = unreal.load_asset(spec['ue_material_path'])
    row = {'material': name, 'path': mat.get_path_name(), 'graph': {}}
    for channel, prop in [('color', unreal.MaterialProperty.MP_BASE_COLOR), ('normal', unreal.MaterialProperty.MP_NORMAL),
                          ('ao', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION), ('roughness', unreal.MaterialProperty.MP_ROUGHNESS)]:
        n = mel.get_material_property_input_node(mat, prop)
        assert n
        stem = spec.get(channel + '_stem')
        if stem:
            tex = n.get_editor_property('texture')
            assert tex.get_name() == stem, (name, channel, tex.get_name(), stem)
            assert tex.get_editor_property('srgb') == (channel == 'color')
            if channel == 'normal':
                assert not tex.get_editor_property('flip_green_channel')
                assert tex.get_editor_property('compression_settings') == unreal.TextureCompressionSettings.TC_NORMALMAP
            row['graph'][channel] = {'texture': tex.get_path_name(), 'srgb': tex.get_editor_property('srgb')}
        else:
            assert abs(n.get_editor_property('r') - spec['roughness_constant']) < 1e-6
            row['graph'][channel] = {'constant': n.get_editor_property('r')}
    assert mat.get_editor_property('used_with_skeletal_mesh') and mat.get_editor_property('used_with_morph_targets')
    rows.append(row)
out = {'pass': True, 'fresh_saved_graph_verification': True, 'materials': rows}
(ROOT / 'Exports/source_character_material_ue_persistence_verify.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
unreal.log('SOURCE_CHARACTER_PRIMARY_PERSISTENCE_PASS ' + json.dumps(out))
