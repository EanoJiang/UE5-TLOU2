"""Sequenced by pipeline: import primary maps and update only jacket/pants.

May run through UE Python commandlet. No level, mesh, skeleton or animation edits.
"""
import json
from pathlib import Path
import unreal

ROOT = Path('D:/TLOU2_UE5_8_Codex')
MANIFEST = json.loads((ROOT / 'Exports/source_character_material_manifest.json').read_text())
DEST = '/Game/TLOU2/TexturesDecoded'
mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()


def texture(stem, channel):
    path = DEST + '/' + stem
    tex = unreal.load_asset(path)
    if not tex:
        task = unreal.AssetImportTask()
        task.filename = str(ROOT / 'Exports/TexturesDecoded' / (stem + '.png'))
        task.destination_path = DEST
        task.destination_name = stem
        task.automated = True
        task.replace_existing = True
        task.save = True
        at.import_asset_tasks([task])
        tex = unreal.load_asset(path)
    assert isinstance(tex, unreal.Texture2D), (stem, tex)
    tex.set_editor_property('srgb', channel == 'color')
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP if channel == 'normal'
                            else unreal.TextureCompressionSettings.TC_DEFAULT if channel == 'color'
                            else unreal.TextureCompressionSettings.TC_MASKS)
    if channel == 'normal':
        tex.set_editor_property('flip_green_channel', False)
    assert unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex


def make_sample(mat, name, tex, channel, y):
    n = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -650, y)
    n.set_editor_property('parameter_name', name)
    n.set_editor_property('texture', tex)
    n.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if channel == 'color'
                          else unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if channel == 'normal'
                          else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    return n


rows = []
for name, spec in MANIFEST['materials'].items():
    mat = unreal.load_asset(spec['ue_material_path'])
    assert isinstance(mat, unreal.Material), name
    textures = {c: texture(spec[c + '_stem'], c) for c in ['color', 'normal', 'ao']}
    if spec['roughness_stem']:
        textures['roughness'] = texture(spec['roughness_stem'], 'roughness')
    mel.delete_all_material_expressions(mat)
    mel.set_base_material_usage(mat, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH, True)
    mel.set_base_material_usage(mat, unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS, True)
    for channel, prop, y in [('color', unreal.MaterialProperty.MP_BASE_COLOR, 0),
                             ('normal', unreal.MaterialProperty.MP_NORMAL, 200),
                             ('ao', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, 400)]:
        n = make_sample(mat, 'ND_' + channel.title(), textures[channel], channel, y)
        assert mel.connect_material_property(n, '' if channel in ['color', 'normal'] else 'R', prop)
    if 'roughness' in textures:
        rough = make_sample(mat, 'ND_SourcePrimary_Roughness', textures['roughness'], 'roughness', 600)
        assert mel.connect_material_property(rough, 'R', unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 600)
        rough.set_editor_property('r', spec['roughness_constant'])
        assert mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.EditorAssetLibrary.set_metadata_tag(mat, 'source_primary_manifest', 'Exports/source_character_material_manifest.json')
    unreal.EditorAssetLibrary.set_metadata_tag(mat, 'source_primary_scope', spec['scope'])
    mel.recompile_material(mat)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(mat))
    assert saved
    graph = {}
    for channel, prop in [('color', unreal.MaterialProperty.MP_BASE_COLOR), ('normal', unreal.MaterialProperty.MP_NORMAL),
                          ('ao', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION), ('roughness', unreal.MaterialProperty.MP_ROUGHNESS)]:
        n = mel.get_material_property_input_node(mat, prop)
        assert n
        if channel == 'roughness' and not spec['roughness_stem']:
            assert abs(n.get_editor_property('r') - spec['roughness_constant']) < 1e-6
            graph[channel] = {'node': n.get_class().get_name(), 'constant': n.get_editor_property('r')}
        else:
            t = n.get_editor_property('texture')
            assert t == textures[channel]
            graph[channel] = {'node': n.get_class().get_name(), 'texture': t.get_path_name(),
                              'srgb': t.get_editor_property('srgb'),
                              'compression': str(t.get_editor_property('compression_settings'))}
    rows.append({'material': name, 'path': mat.get_path_name(), 'saved': saved, 'active_graph': graph,
                 'source_normal_xy_strength_baked': spec['source_normal_strength'], 'graph_normal_strength': 1.,
                 'skeletal_usage': mat.get_editor_property('used_with_skeletal_mesh'),
                 'morph_usage': mat.get_editor_property('used_with_morph_targets'), 'scope': spec['scope']})
report = {'pass': True, 'materials': rows, 'level_mesh_skeleton_animation_edits': False,
          'persistence': 'EditorAssetLibrary.save_loaded_asset returnedTrue for all textures/materials; active graph input nodes verified after save. Fresh editor verification can rerun the companion script.'}
(ROOT / 'Exports/source_character_material_ue_application.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('SOURCE_CHARACTER_PRIMARY_UE_PASS ' + json.dumps(report))
