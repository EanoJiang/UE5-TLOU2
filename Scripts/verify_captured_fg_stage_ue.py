"""Reload the final map and audit persisted FG geometry/material settings."""
import unreal,json
ROOT='D:/TLOU2_UE5_8_Codex'
exec(compile(open(ROOT+'/Scripts/verify_capture_matched_catalog_map_ue.py').read(),ROOT+'/Scripts/verify_capture_matched_catalog_map_ue.py','exec'))
manifest=json.load(open(ROOT+'/Exports/capture_fg_stage_manifest.json'))
imported=json.load(open(ROOT+'/Exports/import_captured_fg_stage_result.json'))
mel=unreal.MaterialEditingLibrary
sub=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem) or unreal.StaticMeshEditorSubsystem()
rows=[]
for path in imported['imported_meshes']:
    mesh=unreal.load_asset(path);settings=sub.get_lod_build_settings(mesh,0)
    assert settings.get_editor_property('use_full_precision_u_vs')
    assert settings.get_editor_property('use_high_precision_tangent_basis')
    slots=[]
    for slot in mesh.get_editor_property('static_materials'):
        mat=slot.get_editor_property('material_interface');assert mat
        slots.append(mat.get_path_name())
    rows.append({'mesh':path,'float32_uvs':True,'high_precision_tangents':True,'materials':slots})
materials=[]
for key,path in imported['materials'].items():
    mat=unreal.load_asset(path);values=manifest['material_maps'][key]
    row={'key':key,'asset':path,'opacity_mask':values[4]}
    if values[4]:
        assert mat.get_editor_property('blend_mode')==unreal.BlendMode.BLEND_MASKED
        assert abs(mat.get_editor_property('opacity_mask_clip_value')-.5)<1e-7
        output=mel.get_material_property_input_node(mat,unreal.MaterialProperty.MP_OPACITY_MASK)
        assert isinstance(output,unreal.MaterialExpressionMultiply)
        # Reimports can leave disconnected editor expression objects. Audit
        # only the dependency graph that actually drives OpacityMask.
        nodes=[];pending=[output];visited=set()
        while pending:
            node=pending.pop()
            if not node or node.get_path_name() in visited:continue
            visited.add(node.get_path_name());nodes.append(node)
            pending.extend(mel.get_inputs_for_material_expression(mat,node))
        masks=[n for n in nodes if isinstance(n,unreal.MaterialExpressionTextureSampleParameter2D) and str(n.get_editor_property('parameter_name'))=='FG_DepthOpacity']
        assert len(masks)==1,(key,len(nodes),[(n.get_class().get_name(),str(n.get_editor_property('parameter_name')) if isinstance(n,unreal.MaterialExpressionTextureSampleParameter2D) else n.get_name()) for n in nodes])
        texture=masks[0].get_editor_property('texture')
        assert texture.get_name()==values[4]
        assert not texture.get_editor_property('srgb')
        k=.6 if 'moss' in key else .3
        assert any(isinstance(n,unreal.MaterialExpressionMultiply) and abs(n.get_editor_property('const_b')-k)<1e-7 for n in nodes)
        assert any(isinstance(n,unreal.MaterialExpressionDistance) for n in nodes)
        assert any(isinstance(n,unreal.MaterialExpressionSquareRoot) for n in nodes)
        row.update({'clip':.5,'distance_factor':k,'formula':'mask.R*max(1,k*sqrt(distanceMeters)) > .5','persisted_graph_pass':True})
    materials.append(row)
report={'pass':True,'stage_meshes':len(rows),'stage_materials':len(materials),'masked_materials':sum(bool(r['opacity_mask']) for r in materials),'rows':rows,'materials':materials,
        'map_stage_identity_and_component_materials_pass':True,
        'scope':'Fresh UE map reload; identity actors, assigned materials, UV/tangent precision and original depthmask distance graph persisted. Does not claim source layered shading or static mesh raw-vertex audit.'}
json.dump(report,open(ROOT+'/Exports/captured_fg_stage_ue_validation.json','w'),indent=2)
unreal.log('CAPTURED_FG_STAGE_PERSISTENCE_PASS '+json.dumps({k:v for k,v in report.items() if k not in ['rows','materials']}))
