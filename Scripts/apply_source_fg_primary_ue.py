"""Source-proven FG primary shader math; no geometry or map edits."""
import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
DEST='/Game/TLOU2/CaptureMatched1152/FGStage'
report=json.load(open(ROOT+'/Exports/import_captured_fg_stage_result.json'))
mel=unreal.MaterialEditingLibrary
rows=[]
def node(mat,cls,label):
    n=mel.create_material_expression(mat,cls,-500,500);n.set_editor_property('desc',label);return n
def link(src,out,dst,inp):
    names=list(mel.get_material_expression_input_names(dst))
    if inp not in names and inp in ['Coordinates','Input','Base']:inp=names[0] if names else ''
    assert mel.connect_material_expressions(src,out,dst,inp),(dst.get_name(),inp,names)
def sample(mat,stem,channel,uv,raw=False):
    source=DEST+'/Textures/'+stem
    if raw:
        target=DEST+'/Textures/SourceRaw_'+stem
        if not unreal.EditorAssetLibrary.does_asset_exist(target):unreal.EditorAssetLibrary.duplicate_asset(source,target)
        texture=unreal.load_asset(target);texture.set_editor_property('srgb',False)
        texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DEFAULT)
        sampler=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    else:
        texture=unreal.load_asset(source);texture.set_editor_property('srgb',False)
        texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if channel=='normal' else unreal.TextureCompressionSettings.TC_MASKS)
        sampler=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if channel=='normal' else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    assert texture,stem;unreal.EditorAssetLibrary.save_loaded_asset(texture)
    n=node(mat,unreal.MaterialExpressionTextureSampleParameter2D,'Original source '+stem)
    n.set_editor_property('parameter_name','FG_SourcePrimary_'+channel);n.set_editor_property('texture',texture);n.set_editor_property('sampler_type',sampler)
    link(uv,'',n,'Coordinates');return n
for key in ['ped-floor-concrete-a','ped-wood-base-trim-a-plain']:
    mat=unreal.load_asset(report['materials'][key]);wood='wood' in key
    uv=node(mat,unreal.MaterialExpressionTextureCoordinate,'Original UV0')
    if wood:
        scale=node(mat,unreal.MaterialExpressionMultiply,'Source UV0 x2');scale.set_editor_property('const_b',2.);link(uv,'',scale,'A');uv=scale
    color=sample(mat,'scar-wood-rough-a-basecolor' if wood else 'concrete-mega-slab-a-alt-color','color',uv,True)
    tint=node(mat,unreal.MaterialExpressionConstant3Vector,'Captured gamma-space tint')
    tint.set_editor_property('constant',unreal.LinearColor(.69,.58,.404,1) if wood else unreal.LinearColor(.5,.5,.5,1))
    encoded=node(mat,unreal.MaterialExpressionMultiply,'Original encoded source color times tint');link(color,'RGB',encoded,'A');link(tint,'',encoded,'B')
    saturation=node(mat,unreal.MaterialExpressionSaturate,'Source saturate');link(encoded,'',saturation,'Input');encoded=saturation
    rough=sample(mat,'scar-wood-rough-a-roughness' if wood else 'concrete-mega-slab-a-roughness','roughness',uv)
    rough_scale=node(mat,unreal.MaterialExpressionMultiply,'Captured primary roughness scale');rough_scale.set_editor_property('const_b',.75 if wood else 2.5);link(rough,'R',rough_scale,'A')
    if not wood:
        squared=node(mat,unreal.MaterialExpressionMultiply,'Wet source encoded color squared');link(encoded,'',squared,'A');link(encoded,'',squared,'B')
        wet=node(mat,unreal.MaterialExpressionLinearInterpolate,'Captured wet strength .3');wet.set_editor_property('const_alpha',.3);link(encoded,'',wet,'A');link(squared,'',wet,'B')
        darken=node(mat,unreal.MaterialExpressionMultiply,'Captured wet amount .35 gives multiplier .985');darken.set_editor_property('const_b',.985);link(wet,'',darken,'A');encoded=darken
        offset=node(mat,unreal.MaterialExpressionAdd,'Captured dry roughness -1 +2.5R');offset.set_editor_property('const_b',-1.);link(rough_scale,'',offset,'A')
        clamp=node(mat,unreal.MaterialExpressionClamp,'Source roughness clamp .005..1');clamp.set_editor_property('min_default',.005);clamp.set_editor_property('max_default',1.);link(offset,'',clamp,'Input')
        rough_wet=node(mat,unreal.MaterialExpressionLinearInterpolate,'Captured wet roughness lerp .1 at .1875');rough_wet.set_editor_property('const_b',.1);rough_wet.set_editor_property('const_alpha',.1875);link(clamp,'',rough_wet,'A');rough_scale=rough_wet
    linear=node(mat,unreal.MaterialExpressionPower,'Original DeferredLighting gamma-to-linear power2.2');linear.set_editor_property('const_exponent',2.2);link(encoded,'',linear,'Base')
    assert mel.connect_material_property(linear,'',unreal.MaterialProperty.MP_BASE_COLOR)
    assert mel.connect_material_property(rough_scale,'',unreal.MaterialProperty.MP_ROUGHNESS)
    if wood:
        normal=sample(mat,'scar-wood-rough-a-normal','normal',uv)
        assert mel.connect_material_property(normal,'RGB',unreal.MaterialProperty.MP_NORMAL)
    mel.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
    rows.append({'key':key,'asset':mat.get_path_name(),'source_color_raw_texture':color.get_editor_property('texture').get_path_name(),
                 'uv_scale':2 if wood else 1,'source_tint':[.69,.58,.404] if wood else [.5,.5,.5],
                 'gamma_to_linear_exponent':2.2,'uniform_wet_amount':None if wood else .35,
                 'primary_source_branch_only':True,'original_layer_blend_attributes_not_fully_ported':True})
out={'pass':True,'materials':rows,'geometry_map_camera_controls_unchanged':True,
     'source_evidence':'Content/TLOU2/Reports/CAPTURE_FG_SOURCE_PRIMARY_SHADER_PARAMS.json',
     'scope':'FG source primary tint/UV/roughness and concrete uniform wet defaults after texture sampling. Preserves original raw gamma texture values then sourcepow2.2. Does not reconstruct complete missing source layer attributes, skin/character shading or lighting.'}
json.dump(out,open(ROOT+'/Exports/source_fg_primary_ue_application.json','w'),indent=2)
unreal.log('SOURCE_FG_PRIMARY_UE_PASS '+json.dumps(out))
