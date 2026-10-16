"""Filesystem-only final material audit; never starts or modifies Unreal."""
import ast,csv,hashlib,json,struct
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Content/TLOU2/Reports'
meta=json.loads((ROOT/'Exports/final_blender_material_metadata.json').read_text())
manifest=json.loads((ROOT/'Exports/TexturesDecoded/texture_decode_manifest.json').read_text())
ue_map=json.loads((ROOT/'Exports/capture_matched_catalog_map_result.json').read_text())
chunks=json.loads((ROOT/'Exports/captured_skin_pose_chunk_manifest.json').read_text())['chunks']
portability=json.loads((ROOT/'Exports/MaterialPortability/Ellie_Patrol_Catalog_CaptureMatched.json').read_text())
tree=ast.parse((ROOT/'Scripts/import_decoded_materials_ue.py').read_text())
maps={}
for node in tree.body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['COLOR','NORMAL','AO','OPACITY']:
        maps[node.targets[0].id]=ast.literal_eval(node.value)
maps['COLOR']['eyes']='ellie-eyes-reconstructed-basecolor'
maps['NORMAL']['eyes']='ellie-eyes-reconstructed-normal'
maps['AO'].pop('eyes',None)
maps['COLOR']['tearduct']='ellie-caruncle-color'
maps['NORMAL']['tearduct']='ellie-caruncle-normal'
maps['NORMAL']['tears']='tear-normal'
character_primary=json.loads((ROOT/'Exports/source_character_material_manifest.json').read_text())
for key,spec in character_primary['materials'].items():
    for channel,field in [('COLOR','color_stem'),('NORMAL','normal_stem'),('AO','ao_stem')]:maps[channel][key]=spec[field]
textures_by_stem={Path(r['decoded_path']).stem:r for r in manifest}
assert len(manifest)==340
assert len(meta['meshes'])==29 and len(meta['materials'])==24
assert ue_map['material_slots']==ue_map['material_bindings']==24
assert sum(m['vertices'] for m in meta['meshes'])==84954
assert all(i['packed'] for i in meta['active_character_images'])
original_texture_audit=[]
for row in manifest:
    path=Path(row['decoded_path'])
    actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    original_texture_audit.append({'name':row['name'],'path':str(path),'hash64_hex':f"{row['hash']:016X}",
                                 'width':row['width'],'height':row['height'],'format':row.get('format_name'),
                                 'png_sha256':actual,'matches_decode_manifest':actual==row.get('png_sha256')})
assert all(r['matches_decode_manifest'] for r in original_texture_audit)
derived={
 'ellie-head-normal-xyz':{'type':'derived normal Z','source':['ellie-head-normal'],'method':'decode RG to[-1,1], reconstruct positive Z; source B is auxiliary'},
 'ellie-eyes-reconstructed-basecolor':{'type':'reconstructed shader output','source':['ellie-eyes-iris-color','ellie-eye-sclera'],'method':'radial iris blend, inferred UV scale3.2 around(.5,.5), linear-light mixing'},
 'ellie-eyes-reconstructed-normal':{'type':'reconstructed shader output','source':['iris-normal'],'method':'same inferred iris UV scale3.2; flat tangent normal outside iris'},
}
for key,spec in character_primary['materials'].items():
    for row in spec['derived_textures']:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['png_sha256']
        derived[row['stem']]={'type':'captured source primary shader bake','source':row['sources'],'method':row['equation'],
                              'source_material':key,'scope':spec['scope'],'path':row['path'],'colorspace':row['colorspace']}
def texture_record(stem):
    if not stem:return None
    path=Path(derived[stem]['path']) if stem in derived and derived[stem].get('path') else ROOT/'Exports/TexturesDecoded'/(stem+'.png')
    if stem in textures_by_stem:
        r=textures_by_stem[stem];d=r.get('dictionary_descriptor',{})
        return {'stem':stem,'decoded_path':str(path),'provenance':'original PC texturedict3 hash match',
                'hash64_hex':f"{r['hash']:016X}",'dimensions':[r['width'],r['height']],
                'format':r.get('format_name'),'png_sha256':r.get('png_sha256'),
                'resident_pak':r['source_pak'],'dictionary_pak':d.get('source_pak'),
                'dictionary_descriptor_offset':d.get('descriptor_offset'),'dictionary_payload_abs':d.get('payload_abs'),
                'decoder':'BC rows aligned256bytes; BGRA decoder output convertedRGBA; BC5 positiveZ reconstructed'}
    if stem not in derived:
        return {'stem':stem,'decoded_path':str(path),'provenance':'configured name absent from decode set',
                'active':False,'file_exists':path.exists(),
                'policy':'Import helper returnsNone for this stem and doesnot connect a texture; no alternate outfit map is silently substituted.'}
    return {'stem':stem,'decoded_path':str(path),'provenance':derived[stem]['type'],
            'png_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**derived[stem]}
ue_bindings={s['slot']:s['material'] for actor in ue_map['actors'] for s in actor['materials']}
mesh_chunk={m['source_mesh']:chunk for chunk,row in chunks.items() for m in row['meshes']}
notes={
 'eyes':['Original iris and sclera maps are preserved; radial UV scale3.2 is inferred, not an extracted shader constant.','Portable normal/basecolor composite; original corneal refraction, parallax and wetness optics are not ported.'],
 'head':['Original basecolor and RG normal are used; positive normal Z is derived.','Generic PBR; no original facial wrinkle blending, subsurface profile, blood or wetness layer is claimed.'],
 'tearduct':['Original ellie-caruncle-color/normal mapped in Blender and UE; generic PBR roughness.8.'],
 'tears':['Original tear-normal selected consistently with UE. Two original tear-normal hashes exist; exact source shader binding remains unresolved.','Portable film uses alpha.08 and roughness.12; UE translucent and Blender dithered. Original tear refraction and flow are not ported.'],
 'eyelashes':['Original normal/transparency maps; constant basecolor.18; UE mask threshold.25 and two-sided.'],
 'pants':['Actual captured t2 is byte-identical to ellie-festival-pants-ao; this proven reuse supersedes the earlier missing-wetness-mask AO configuration.','Captured primary color is clamp(2*1.1*rawRGB*(1,.965,.906)), then pow2.2; baked portable color uses standard sRGB encoding. Primary roughness.67; complex overlays remain approximate.'],
 'jacket':['Actual captured normal is BC5 hash36950F2112783B58; the earlier BC7 normal selection is superseded.','Captured primary encoded color=2*rawRGB*(.973,.91,.91), clamped then pow2.2. BC5signedXY is scaled1.3 and Z reconstructed before baking; DCC/UE graph applies no second normal strength.','Primary roughness lerp(.88,.5,saturate(1-metallic.R)); complete original detail/wet/snow layers and source TBN orientation remain unverified.'],
}
materials=[]
for name,blender in sorted(meta['materials'].items()):
    key=blender['source_material_key']
    mapped={channel:texture_record(maps[channel].get(key)) for channel in ['COLOR','NORMAL','AO','OPACITY']}
    rough=.18 if key=='eyes' else (.12 if key=='tears' else (.9 if 'hair' in key else (.64 if key in ['head','arms'] else .8)))
    spec=character_primary['materials'].get(key)
    rough_texture=texture_record(spec['roughness_stem']) if spec and spec['roughness_stem'] else None
    if spec:rough=spec['roughness_constant']
    material_notes=list(notes.get(key,[]))
    if 'hair' in key:
        material_notes+=['Original color/normal/transparency maps with separate maskR, threshold.25, two-sided.','Generic roughness.9 PBR; original strand anisotropy, dual scattering and capture hair-color profile are not claimed.']
    if not material_notes:material_notes=['Original decoded maps connected through portable PBR; source layered/wetness/detail shader behavior is not fully ported.']
    status='original texture maps + reconstructed portable shader'
    if key=='eyes':status='original maps + explicitly reconstructed radial eye shader'
    materials.append({'material':name,'key':key,'ue_material_path':ue_bindings[name],
                      'configured_ue_textures':mapped,'configured_ue_roughness':rough,
                      'configured_ue_roughness_texture':rough_texture,'source_primary_equations':spec['formulas'] if spec else None,
                      'configured_ue_blend':'translucent' if key=='tears' else ('masked' if maps['OPACITY'].get(key) else 'opaque'),
                      'configured_opacity_constant':.08 if key=='tears' else None,
                      'configured_mask_threshold':.25 if maps['OPACITY'].get(key) else None,
                      'shader_status':status,'notes':material_notes,'canonical_blender':blender,
                      'verification_scope':'UE material binding verified by saved map; jacket/pants active source-primary graph also has fresh-process persistence verification. Other graph configuration is traced from import/repair scripts.'})
by_material={m['material']:m for m in materials}
meshes=[]
for source in meta['meshes']:
    row={**source,'chunk':mesh_chunk[source['object']],
         'source_pak_path':str(Path('D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97')/source['source_pak']),
         'ue_skeletal_mesh':'/Game/TLOU2/CaptureMatched1152/CapturedMeshes/'+mesh_chunk[source['object']]+'/Ellie_Patrol_'+mesh_chunk[source['object']]+'_Pruned',
         'ue_material_paths':[by_material[m]['ue_material_path'] for m in source['materials']]}
    meshes.append(row)
source_paks=[]
for name in sorted({m['source_pak'] for m in meshes}):
    path=Path('D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97')/name
    source_paks.append({'pak':name,'path':str(path),'exists':path.exists(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                        'selected_mesh_count':sum(m['source_pak']==name for m in meshes)})
glb=ROOT/'Exports/Ellie_Patrol_Catalog_CaptureMatched.glb'
data=glb.read_bytes();length,kind=struct.unpack_from('<II',data,12)
gltf=json.loads(data[20:20+length])
glb_images=[{'name':r.get('name'),'mimeType':r.get('mimeType'),'embedded':'bufferView' in r,'external_uri':r.get('uri')} for r in gltf.get('images',[])]
assert all(r['embedded'] and not r['external_uri'] for r in glb_images)
stage=json.loads((ROOT/'Exports/capture_fg_stage_manifest.json').read_text())
stage_ue=json.loads((ROOT/'Exports/import_captured_fg_stage_result.json').read_text())
stage_texture_manifest=json.loads((ROOT/'Exports/CapturedFGStage/TexturesDecoded/texture_decode_manifest.json').read_text())
stage_texture_audit=[]
for row in stage_texture_manifest:
    path=Path(row['decoded_path']);actual=hashlib.sha256(path.read_bytes()).hexdigest()
    stage_texture_audit.append({'path':str(path),'png_sha256':actual,'matches_decode_manifest':actual==row['png_sha256']})
assert len(stage_texture_audit)==206 and all(r['matches_decode_manifest'] for r in stage_texture_audit)
stage_shader_evidence=json.loads((OUT/'CAPTURE_FG_STAGE_MATERIAL_TEXTURE_BINDINGS.json').read_text())
report={'schema':'tlou2.final_material_mapping.v1','generated_date':'2026-10-16',
        'canonical_blend':meta['blend'],'neutral_fbx':str(ROOT/'Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx'),'neutral_glb':str(glb),
        'selection':{'meshes':29,'vertices':84954,'bones':1152,'materials':24,'ue_bound_material_slots':24,'ue_total_material_slots':24},
        'original_texture_decode_audit':{'manifest_entries':340,'hash_matched_dictionary_entries':340,
            'png_files_verified_against_decode_sha256':340,'pass':True,'derived_character_maps':derived,
            'entries':original_texture_audit},
        'source_paks':source_paks,'meshes':meshes,'materials':materials,
        'source_portability':{'canonical_used_images_including_stage':portability['used_image_count'],
            'canonical_packed_images_including_stage':portability['packed_image_count'],
            'active_character_images':len(meta['active_character_images']),
            'active_character_images_packed':sum(i['packed'] for i in meta['active_character_images']),
            'missing_active_images':meta['portability']['missing_active_images'],
            'absolute_external_active_images':meta['portability']['absolute_external_active_images'],
            'geometry_actions_unchanged':portability['geometry_actions_unchanged'],
            'glb_embedded_image_count':len(glb_images),'glb_images':glb_images,
            'fbx_texture_policy':'CharacterFBX uses Exports/TexturesDecoded; standaloneFGFBX uses Exports/CapturedFGStage/TexturesDecoded and TexturesDerived. Preserve the entire Exports/CapturedFGStage subtree. Blender and GLB embed active images.'},
        'stage_materials':{'selected_meshes':stage['meshes'],'source_vertices':stage['vertices'],'source_materials':stage['materials'],
                           'baseline_source_map_selection':stage['material_maps'],'ue_material_paths':stage_ue['materials'],
                           'portable_primary_overrides':json.loads((ROOT/'Exports/CapturedFGStage/TexturesDerived/derived_texture_manifest.json').read_text()),
                           'ue_primary_override_application':json.loads((ROOT/'Exports/source_fg_primary_ue_application.json').read_text()),
                           'source_pak':stage['source_pak'],'world_matrix_policy':stage['matrix_policy'],
                           'original_texture_entries':206,'png_sha256_verified':206,'texture_audit':stage_texture_audit,
                           'actual_gbuffer_texture_binding_subsets':stage_shader_evidence['source_subsets_with_original_GBuffer_texture_binding_map'],
                           'depth_opacity_evidence':stage_shader_evidence['depth_prepass_opacity'],
                           'ue_opacity_formula':'mask.R*max(1,k*sqrt(cameraDistanceMeters)) > .5; k=.3 fern / .6 moss; global bias0',
                           'dcc_opacity_policy':'Original separate mask R, fixed clip.5 in portable Blender/GLB stage; distance-dependent threshold is implemented in UE.',
                           'policy':'All33 actualFGsubsets, original16jointskin+graphicsinstanceworldbaked, identityactors. PrimarymapsselectedfromactualGBufferbindings when proven; complexlayeredground/detail/UVshader remains portablePBR.'},
        'limitations':['This is a faithful source-geometry/texture mapping with a portable shader reconstruction, not a complete port of every original Naughty Dog material shader.',
                       'Dynamic wrinkle/skin SSS, cloth wetness/detail blending, hair fiber optics, corneal optics and tear flow/refraction remain approximate.',
                       'Mask source channels and color spaces are preserved, but Blender dithered alpha and UE masked/translucent alpha can differ visually.',
                       'Texture table covers340 original decode entries, including unused variants; only the mapped subset drives the final29 visible meshes.'],
        'evidence':['Exports/final_blender_material_metadata.json','Exports/capture_matched_catalog_map_result.json','Exports/TexturesDecoded/texture_decode_manifest.json',
                    'Exports/MaterialPortability/Ellie_Patrol_Catalog_CaptureMatched.json','Exports/neutral_fbx_roundtrip_validation.json',
                    'Exports/Ellie_Patrol_Catalog_CaptureMatched_gltf_skin_validation.json','Scripts/import_decoded_materials_ue.py','Scripts/apply_reconstructed_eye_material_ue.py',
                    'Exports/capture_fg_stage_manifest.json','Exports/import_captured_fg_stage_result.json','Exports/captured_fg_stage_ue_validation.json',
                    'Content/TLOU2/Reports/CAPTURE_FG_STAGE_MATERIAL_TEXTURE_BINDINGS.json','Scripts/import_captured_fg_stage_ue.py']}
report['source_character_primary']=character_primary
report['evidence']+=['Exports/source_character_material_manifest.json','Exports/source_character_material_blender_application.json',
    'Exports/source_character_material_ue_application.json','Exports/source_character_material_ue_persistence_verify.json',
    'Content/TLOU2/Reports/CAPTURE_CHARACTER_SOURCE_PRIMARY_SHADER_PARAMS.json','Content/TLOU2/Reports/CAPTURE_FG_SOURCE_PRIMARY_SHADER_PARAMS.json',
    'Exports/source_fg_primary_ue_validation.json']
(OUT/'MATERIAL_MAPPING_FINAL.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
fields=['mesh','source_pak','source_submesh','vertices','joint_owner','chunk','material','ue_material','color','normal','ao_input','opacity','roughness','blend','shader_status','notes']
with (OUT/'MATERIAL_MAPPING_FINAL.csv').open('w',newline='',encoding='utf-8-sig') as stream:
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    for row in meshes:
        for name in row['materials']:
            mat=by_material[name];tex=mat['configured_ue_textures']
            writer.writerow({'mesh':row['object'],'source_pak':row['source_pak'],'source_submesh':row['source_submesh'],
                             'vertices':row['vertices'],'joint_owner':row['joint_owner'],'chunk':row['chunk'],
                             'material':name,'ue_material':mat['ue_material_path'],
                             'color':tex['COLOR']['stem'] if tex['COLOR'] else '(constant .18)',
                             'normal':tex['NORMAL']['stem'] if tex['NORMAL'] else '',
                             'ao_input':tex['AO']['stem'] if tex['AO'] else '',
                             'opacity':tex['OPACITY']['stem'] if tex['OPACITY'] else ('constant .08' if mat['key']=='tears' else ''),
                             'roughness':mat['configured_ue_roughness_texture']['stem'] if mat['configured_ue_roughness_texture'] else mat['configured_ue_roughness'],'blend':mat['configured_ue_blend'],
                             'shader_status':mat['shader_status'],'notes':' | '.join(mat['notes'])})
def stem(r):return (r['stem']+' (absent; unconnected)' if r.get('active') is False else r['stem']) if r else '—'
lines=['# 最终材质映射与验证','',
       '最终活动角色为 **29 个网格、84,954 个顶点、1,152 根骨骼、24 个材质**。保存的 UE 地图报告确认 **24/24 材质槽已绑定**。角色和帽衫的蒙皮验证另见骨架/截帧报告；本报告只陈述材质与贴图的证据。','',
       '340 条原始贴图均由 `texturedict3` 哈希匹配取得高分辨率数据，本次逐文件重新计算 PNG SHA-256，**340/340 与解码清单一致**。额外的头部 XYZ 法线及两张眼球复合图属于派生资源，不计作新的原始贴图。','',
       '## 角色材质','',
       '下表来自最终 Blender 材质节点与 UE 导入/修复脚本；UE 路径绑定由保存的地图报告核对。纹理图连接的配置来源可追溯，未在本次文件系统任务中重新读取 UE 材质图。CSV 按最终 29 个网格逐行列出原始 PAK、子网格与对应材质。','',
       '| 材质 | 颜色 | 法线 | UE AO 输入 | 透明度 | UE 粗糙度 / 混合 |','|---|---|---|---|---|---|']
for m in materials:
    t=m['configured_ue_textures'];alpha=stem(t['OPACITY']) if t['OPACITY'] else ('常数 .08' if m['key']=='tears' else '—')
    roughness=stem(m['configured_ue_roughness_texture']) if m['configured_ue_roughness_texture'] else str(m['configured_ue_roughness'])
    lines.append('| '+m['key']+' | '+stem(t['COLOR'])+' | '+stem(t['NORMAL'])+' | '+stem(t['AO'])+' | '+alpha+' | '+roughness+' / '+m['configured_ue_blend']+' |')
lines+=['','## 原始资源归属','','| PAK | 最终网格数 |','|---|---|']
for p in source_paks:lines.append('| '+p['pak']+' | '+str(p['selected_mesh_count'])+' |')
lines+=['','完整 PAK SHA-256、原始贴图哈希、字典描述符/负载偏移、PNG SHA-256 及每个网格的 UE 资产路径保存在 JSON。成年角色背包 `ellie-backpack.pak` 与其混合权重格式已按实际 GPU 顶点记录确认；旧的 `backpack-ellie.pak` 道具变体不属于活动清单。','',
       '## 明确保留的 shader 重建范围','',
       '- 眼球：原始虹膜、巩膜及法线贴图经过径向复合；**UV 缩放 3.2 为推定参数**。没有宣称原始角膜折射、视差或湿润光学已移植。',
       '- 头发：原始颜色/法线/透明度贴图，UE 独立 R 通道遮罩、阈值 .25、双面、粗糙度 .9。原始纤维各向异性及多重散射使用通用 PBR 近似。',
       '- 泪膜：使用当前 UE 选择的原始 `tear-normal`，透明度 .08、粗糙度 .12；Blender 使用抖动透明，UE 使用半透明。存在两个原始同名法线哈希，精确 shader 绑定未解明；未宣称原始流动或折射行为。',
       '- 泪阜：原始 `ellie-caruncle-color/normal` 已同步到 Blender 与 UE，粗糙度为通用 PBR 参数。',
       '- 外套、裤子：按实际捕获绑定恢复主层颜色倍率、RGB钳制及源2.2转换；可移植色图另行标准sRGB编码，图内不再重复乘色或转换。外套采用原始BC5法线hash36950F2112783B58，signedXY×1.3后重建Z并归一化，再烘焙为XYZ，DCC/UE法线节点强度为1。外套粗糙度依据源metallic.R遮罩在.88与.5间混合；裤子主层粗糙度.67。',
       '- 裤子AO：实际捕获t2与 `ellie-festival-pants-ao` 压缩字节一致，采用该已证实的源复用；此前未连接的wetness-mask配置已被取代。角色原始NPZ不含独立顶点法线/切线，法线绿色通道与原始TBN方向没有单独验证。原始细节、湿润、泥、雪层以及皮肤SSS仍为近似。',
       '- 展台：33 个原始 FG 子网格、101,538 个分配顶点、27 个材质、206 张原始解码贴图（SHA-256 全部核对）。33 个实际 GBuffer 子集的贴图绑定独立保留；活动混凝土地面原始颜色为 `concrete-mega-slab-a-alt-color`。16 节点蒙皮与实际图形实例矩阵已烘焙进世界坐标，UE 以单位变换导入。',
       '- 蕨叶与苔藓的独立遮罩来自原始深度预通道，并非颜色图 Alpha。UE 使用 `mask.R*max(1,k*sqrt(distanceMeters)) > .5`，蕨叶 k=.3、苔藓 k=.6、偏移为 0；Blender/GLB 地台仅使用固定 .5 阈值。原始地面裂缝、碎石、草地、土壤、落叶等复杂分层以及湿润、细节、UV shader 保留证据，通用 PBR 尚未完整移植。','',
       '- 地台主层：混凝土源gamma色×.5，按捕获湿润强度.3与湿润量.35混合C/C²并乘.985，然后源pow2.2；粗糙度按源范围与湿润公式恢复。木底座改为实际SCAR主层，源颜色乘(.69,.58,.404)、UV×2、粗糙度R×.75。UE在采样后计算，DCC/独立交换使用逐纹素烘焙及8bit量化近似；完整源混层仍未移植。','',
       '## 源文件可移植性','',
       f"中性 Blender 文件已打包 **{portability['packed_image_count']}/{portability['used_image_count']}** 张活动角色/展台图片；其中角色使用的 **{sum(i['packed'] for i in meta['active_character_images'])}/{len(meta['active_character_images'])}** 张图片已嵌入，缺失文件 **0**，活动绝对外部路径 **0**。打包前后几何、骨骼、动作及帧区间签名完全一致。",
       f"重新导出的角色 GLB 含 **{len(glb_images)}** 张内嵌图片，无外部图片 URI。FBX 使用外部 PNG 媒体，角色文件需保留 `Exports/TexturesDecoded`，独立 FG 地台文件需保留整个 `Exports/CapturedFGStage` 子目录（含 `TexturesDecoded` 与 `TexturesDerived`），保持相对于 FBX 的路径。动作 Blender 文件可使用 `apply_final_material_portability_blender.py -- <blendpath>` 应用同一打包与泪阜/泪膜同步，最终动作文件状态由各自的 `Exports/MaterialPortability/*.json` 记录。",'',
       '可机读明细：[MATERIAL_MAPPING_FINAL.json](MATERIAL_MAPPING_FINAL.json)；网格逐项表：[MATERIAL_MAPPING_FINAL.csv](MATERIAL_MAPPING_FINAL.csv)。','']
(OUT/'MATERIAL_MAPPING_FINAL.md').write_text('\n'.join(lines),encoding='utf-8')
print('FINAL_MATERIAL_REPORT',json.dumps({'meshes':29,'vertices':84954,'materials':24,'original_png_sha256_verified':340,'packed_character_images':sum(i['packed'] for i in meta['active_character_images']),'packed_all_used_images':portability['packed_image_count'],'glb_embedded_images':len(glb_images)}))
