"""Read back the source-backed FG shader graphs in a fresh UE process."""
import unreal,json,hashlib
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
application=json.loads((ROOT/'Exports/source_fg_primary_ue_application.json').read_text())
mel=unreal.MaterialEditingLibrary
rows=[]
def closure(mat,output):
    found=[];todo=[output];seen=set()
    while todo:
        node=todo.pop()
        if not node or node.get_path_name() in seen:continue
        seen.add(node.get_path_name());found.append(node);todo.extend(mel.get_inputs_for_material_expression(mat,node))
    return found
for source in application['materials']:
    mat=unreal.load_asset(source['asset']);wood='wood' in source['key']
    color=mel.get_material_property_input_node(mat,unreal.MaterialProperty.MP_BASE_COLOR)
    assert isinstance(color,unreal.MaterialExpressionPower) and abs(color.get_editor_property('const_exponent')-2.2)<1e-6
    color_nodes=closure(mat,color)
    samples=[n for n in color_nodes if isinstance(n,unreal.MaterialExpressionTextureSampleParameter2D)]
    assert len(samples)==1
    texture=samples[0].get_editor_property('texture');assert texture.get_path_name()==source['source_color_raw_texture']
    assert not texture.get_editor_property('srgb')
    assert samples[0].get_editor_property('sampler_type')==unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    tint=next(n.get_editor_property('constant') for n in color_nodes if isinstance(n,unreal.MaterialExpressionConstant3Vector))
    assert max(abs(v-w) for v,w in zip([tint.r,tint.g,tint.b],source['source_tint']))<1e-6
    rough=mel.get_material_property_input_node(mat,unreal.MaterialProperty.MP_ROUGHNESS)
    rough_nodes=closure(mat,rough)
    if wood:
        assert isinstance(rough,unreal.MaterialExpressionMultiply) and abs(rough.get_editor_property('const_b')-.75)<1e-7
        assert any(isinstance(n,unreal.MaterialExpressionMultiply) and abs(n.get_editor_property('const_b')-2)<1e-7 for n in color_nodes)
        normal=mel.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL)
        assert isinstance(normal,unreal.MaterialExpressionTextureSampleParameter2D) and normal.get_editor_property('texture').get_name()=='scar-wood-rough-a-normal'
    else:
        assert isinstance(rough,unreal.MaterialExpressionLinearInterpolate) and abs(rough.get_editor_property('const_alpha')-.1875)<1e-7
        assert any(isinstance(n,unreal.MaterialExpressionLinearInterpolate) and abs(n.get_editor_property('const_alpha')-.3)<1e-7 for n in color_nodes)
        assert any(isinstance(n,unreal.MaterialExpressionMultiply) and abs(n.get_editor_property('const_b')-.985)<1e-7 for n in color_nodes)
        assert any(isinstance(n,unreal.MaterialExpressionClamp) and abs(n.get_editor_property('min_default')-.005)<1e-7 for n in rough_nodes)
    package=source['asset'].split('.')[0];file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset')
    rows.append({'key':source['key'],'asset':source['asset'],'asset_file':str(file),'asset_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                 'source_equations_persisted':True,'source_raw_texture_srgb':False,'source_gamma_exponent':2.2})
out={'pass':True,'materials':rows,'scope':'Fresh-process graph readback of captured primary tint/gamma/UV/roughness/wet equations. Complete original layer masks and source pixel identity remain outside scope.'}
(ROOT/'Exports/source_fg_primary_ue_validation.json').write_text(json.dumps(out,indent=2))
unreal.log('SOURCE_FG_PRIMARY_PERSISTENCE_PASS '+json.dumps(out))
