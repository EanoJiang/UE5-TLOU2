"""Regenerate canonical Chinese delivery docs from current evidence.

No Unreal or Blender process is started. Failed, stale or absent runtime
validation remains pending. Only an explicit allowlist of delivery artifacts is
hashed; capture page/chunk caches and historical experiments are excluded.
"""
import csv,hashlib,json,math,os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/'Content/TLOU2/Reports'
REPORTS.mkdir(parents=True,exist_ok=True)
CAPTURE='D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture'
EDITOR='D:/EpicGame/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
MAP='/Game/TLOU2/Maps/ElliePatrolCaptureMatched'
NOW=datetime.now(timezone.utc).isoformat()
HASH_CACHE={}

def read(rel):
    path=ROOT/rel
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except (FileNotFoundError,json.JSONDecodeError):return {}

def hash_file(path):
    path=Path(path)
    if not path.exists() or not path.is_file():return None
    stat=path.stat();key=(str(path),stat.st_size,stat.st_mtime_ns)
    if key not in HASH_CACHE:
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        HASH_CACHE[key]=digest.hexdigest()
    return HASH_CACHE[key]

def passed(doc):return doc.get('pass') is True or doc.get('pass_') is True
def relpath(path):return Path(path).relative_to(ROOT).as_posix()
def link(path,label=None,base=ROOT):
    path=ROOT/path if not Path(path).is_absolute() else Path(path)
    target=os.path.relpath(path,base).replace('\\','/')
    return '['+(label or path.name)+']('+target+')'
def number(value,scale=1):return '未提供' if value is None else f'{float(value)*scale:.6g}'

MODELS=[
 {'id':'neutral','label':'绑定参考姿态 / 中性模型','stem':'Ellie_Patrol_Catalog_CaptureMatched','role':'原始参考绑定与全部12路蒙皮；后续编辑从此开始。'},
 {'id':'captured','label':'截帧静态姿态','stem':'Ellie_Patrol_CapturedSkinPose','role':'截帧骨骼矩阵与静态仿射修正；用于目标图鉴展示。'},
 {'id':'viewer','label':'原始图鉴姿态','stem':'Ellie16_Patrol_OriginalViewerPose','role':'原始520骨骼、1帧姿态；UE使用两帧相同保持样本。'},
 {'id':'0fw','label':'原始0FW动画','stem':'Ellie_Patrol_Original_0FW','role':'26骨骼、80帧、30Hz的右臂/手指稀疏动画层。'},
]
for model in MODELS:
    model['blend']='Blender/'+model['stem']+'.blend'
    model['fbx']='Exports/'+model['stem']+'.fbx'
    model['glb']='Exports/'+model['stem']+'.glb'
    model['gltf']='Exports/'+model['stem']+'.gltf'
    model['bin']='Exports/'+model['stem']+'.bin'

runtime_path='Exports/ue_runtime_capture_vertex_validation.json'
runtime=read(runtime_path)
dump_path=Path(runtime.get('ue_runtime_dump',str(ROOT/'Exports/UERuntimeCapturedVertices/ue_runtime_vertex_dump.json')))
runtime_fresh=bool(runtime and dump_path.exists() and (ROOT/runtime_path).stat().st_mtime_ns>=dump_path.stat().st_mtime_ns)
runtime_pass=passed(runtime) and runtime_fresh
runtime_status='通过（最新运行时数值报告）' if runtime_pass else '待完成（尚无最新通过报告）'
runtime_detail='原始shader权重参考最大位置误差 '+number(runtime.get('original_shader_bidirectional_max_distance_m',runtime.get('bidirectional_max_distance_m')),1000)+' mm；阈值 '+number(runtime.get('tolerance_m'),1000)+' mm。'
if runtime and not runtime_fresh:runtime_detail+=' 当前报告早于最新运行时导出，不能作为最新结果。'

raw=read('Exports/captured_pose_independent_raw_vertex_validation.json')
raw_fresh=bool(raw.get('source_blend_sha256')) and hash_file(Path(raw['source_blend']))==raw['source_blend_sha256'] and hash_file(Path(raw['reference']))==raw.get('reference_sha256')
gltf=read('Exports/captured_gltf_independent_pose_validation.json')
gltf_fresh=bool(gltf.get('glb_sha256') and hash_file(ROOT/'Exports/Ellie_Patrol_CapturedSkinPose.glb')==gltf['glb_sha256'])
gltf_pass=passed(gltf) and gltf_fresh
fbx=read('Exports/neutral_fbx_roundtrip_validation.json')
fbx_all=read('Exports/canonical_fbx_fidelity_validation.json')
fbx_all_fresh=len(fbx_all.get('files',[]))==4 and all(hash_file(Path(r['file']))==r.get('sha256') and hash_file(Path(r['source_blend']))==r.get('source_blend_sha256') for r in fbx_all.get('files',[]))
root_motion=read('Exports/final_root_motion_transform_validation.json')
root_motion_fresh=len(root_motion.get('files',[]))==3 and all(hash_file(Path(r['csv']))==r.get('csv_sha256') and hash_file(Path(r['source_blend']))==r.get('source_blend_sha256') for r in root_motion.get('files',[]))
material=read('Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.json')
source_validation=read('Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_reference_verification.json')
codec=read('Content/TLOU2/Reports/TARGET_0FW_COMPLETE_DECODE_VALIDATION.json')
viewer_native=read('Content/TLOU2/Reports/MODEL_VIEWER_NATIVE_CONSTANT_VERIFICATION.json')
ue0=read('Exports/original_0fw_ue_transform_validation.json')
ueviewer=read('Exports/original_viewer_ue_transform_validation.json')
controls=read('Exports/catalog_controls_validation.json')
map_validation=read('Exports/capture_matched_catalog_map_validation.json')
morph=read('Exports/captured_corrective_curve_validation.json')
usage=read('Exports/final_material_usage_persistent_validation.json')
mesh_material_sync=read('Exports/captured_mesh_scene_material_sync_validation.json')
mesh_material_sync_fresh=passed(mesh_material_sync) and all(
    hash_file(ROOT/'Content'/(row['mesh'].split('.')[0].removeprefix('/Game/')+'.uasset'))==row.get('saved_asset_sha256')
    for row in mesh_material_sync.get('meshes',[]))
camera=read('Content/TLOU2/Reports/CAPTURE_ORIGINAL_CAMERA_CONSTANTS.json')
stage=read('Exports/capture_fg_stage_validation.json')
stage_manifest=read('Exports/capture_fg_stage_manifest.json')
stage_ue=read('Exports/captured_fg_stage_ue_validation.json')
stage_exchange=read('Exports/captured_fg_stage_exchange_validation.json')
stage_exchange_fresh=bool(stage_exchange.get('files')) and all(hash_file(Path(row['file']))==row.get('sha256') for row in stage_exchange.get('files',[]))
stage_pass=passed(stage) and passed(stage_ue) and passed(stage_exchange) and stage_exchange_fresh and stage_ue.get('stage_meshes')==33 and map_validation.get('stage_actor_count')==33
stage_status='通过（33个原始FG网格、截帧矩阵与UE持久化）' if stage_pass else '待完成（原始FG展台正在核验）'
triangles=read('Content/TLOU2/Reports/CAPTURE_CHARACTER_TRIANGLE_INDEX_VALIDATION.json')
compression=read('Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_verification.json')
glb_animation=read('Exports/original_animation_glb_sample_validation.json')
glb_animation_fresh=len(glb_animation.get('clips',[]))==2 and all(hash_file(Path(r['glb']))==r.get('glb_sha256') and hash_file(Path(r['source']))==r.get('source_sha256') for r in glb_animation.get('clips',[]))
skin_reports=[read('Exports/'+m['stem']+'_gltf_skin_validation.json') for m in MODELS]
skin_reports_fresh=all(r.get('file_sha256') and hash_file(Path(r['file']))==r['file_sha256'] for r in skin_reports)
fg_primary=read('Exports/source_fg_primary_ue_validation.json')
fg_primary_fresh=bool(fg_primary.get('materials')) and all(hash_file(Path(r['asset_file']))==r.get('asset_sha256') for r in fg_primary.get('materials',[]))
character_primary=read('Exports/source_character_material_ue_persistence_verify.json')

trajectories=[]
for model in MODELS[1:]:
    rel='Exports/'+model['stem']+'_RootTrajectory.csv'
    path=ROOT/rel
    row={'path':rel,'model':model['id'],'exists':path.exists()}
    if path.exists():
        samples=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
        if samples:
            axes=['root_x_m','root_y_m','root_z_m']
            first=[float(samples[0][k]) for k in axes]
            row.update({'samples':len(samples),'maximum_displacement_m':max(math.dist(first,[float(s[k]) for k in axes]) for s in samples)})
            row['zero_displacement']=row['maximum_displacement_m']<1e-10
    trajectories.append(row)

previews=[
 {'path':'Exports/Ellie_Patrol_NeutralModel_Preview.png','label':'中性模型预览 PNG','role':'Blender参考绑定姿态'},
 {'path':'Exports/Ellie_Patrol_CapturedSkinPose_Preview.png','label':'截帧姿态模型预览 PNG','role':'Blender原始相机预览，外观仍含材质近似'},
 {'path':'Exports/Ellie_Patrol_UE_Runtime.png','label':'UE实际RHI截图 PNG','role':runtime_status+'；文件存在不等于外观或数值验证通过'},
 {'path':'Exports/Ellie_Patrol_Original0FW_Preview.png','label':'0FW动画预览 PNG','role':'原始稀疏动画层'},
 {'path':'Exports/Ellie_Patrol_Original0FW_AnimationPreview.gif','label':'原始0FW动画预览 GIF','role':'全部80源帧；GIF以30/40ms帧延时分布近似30Hz，配套报告记录逐帧时间'},
]
preview_reports=[read('Exports/'+stem) for stem in ['Ellie_Patrol_NeutralModel_Preview_report.json','Ellie_Patrol_CapturedSkinPose_Preview_report.json','Ellie_Patrol_Original0FW_AnimationPreview_report.json']]
previews_fresh=all(r.get('source_blend_sha256') and hash_file(Path(r.get('source_blend',r.get('blend',''))))==r['source_blend_sha256'] and hash_file(Path(r['png']))==r.get('png_sha256') and r.get('stage_meshes')==33 for r in preview_reports)
gif_report=preview_reports[-1]
gif_fresh=bool(gif_report.get('gif_sha256')) and hash_file(Path(gif_report['gif']))==gif_report['gif_sha256'] and len(gif_report.get('rendered_frames',[]))==80 and gif_report.get('gif_duration_ms')==2670

EVIDENCE=[
 'Exports/captured_mesh_scene_material_sync_application.json','Exports/captured_mesh_scene_material_sync_validation.json',
 'Scripts/sync_captured_mesh_scene_materials_ue.py',
 'Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.md','Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.json','Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.csv',
 'Content/TLOU2/Reports/CAPTURE_MESH_SOURCE_BINDING_VALIDATION.md','Content/TLOU2/Reports/CAPTURE_MESH_SOURCE_BINDING_VALIDATION.json',
 'Content/TLOU2/Reports/CAPTURE_CHARACTER_TRIANGLE_INDEX_VALIDATION.md','Content/TLOU2/Reports/CAPTURE_CHARACTER_TRIANGLE_INDEX_VALIDATION.json',
 'Content/TLOU2/Reports/CAPTURE_FG_STAGE_VALIDATION.md','Content/TLOU2/Reports/CAPTURE_FG_STAGE_INDEX_INSTANCE_VALIDATION.json',
 'Content/TLOU2/Reports/CAPTURE_FG_STAGE_MATERIAL_TEXTURE_BINDINGS.json',
 'Content/TLOU2/Reports/CAPTURE_ORIGINAL_CAMERA_CONSTANTS.md','Content/TLOU2/Reports/CAPTURE_ORIGINAL_CAMERA_CONSTANTS.json',
 'Content/TLOU2/Reports/CAPTURE_SHADER_SKINNING.md','Content/TLOU2/Reports/TARGET_0FW_COMPLETE_DECODE_VALIDATION.json',
 'Content/TLOU2/Reports/MODEL_VIEWER_NATIVE_CONSTANT_VERIFICATION.json',
 'Exports/captured_pose_independent_raw_vertex_validation.json','Exports/captured_gltf_independent_pose_validation.json',
 'Exports/neutral_fbx_roundtrip_validation.json','Exports/Ellie_Patrol_Catalog_CaptureMatched_gltf_skin_validation.json',
 'Exports/canonical_fbx_fidelity_validation.json',
 'Exports/original_animation_glb_sample_validation.json',
 'Exports/final_root_motion_transform_validation.json',
 'Exports/restored_body_reimport_ue_validation.json','Exports/restored_body_chunk_export_validation.json',
 'Exports/source_fg_primary_ue_application.json',
 'Exports/source_fg_primary_ue_validation.json','Exports/portable_gltf_fidelity_exporter_blender52.json',
 'Exports/source_character_material_manifest.json','Exports/source_character_material_blender_application.json',
 'Exports/source_character_material_ue_application.json','Exports/source_character_material_ue_persistence_verify.json',
 'Content/TLOU2/Reports/CAPTURE_CHARACTER_SOURCE_PRIMARY_SHADER_PARAMS.json','Content/TLOU2/Reports/CAPTURE_CHARACTER_SOURCE_PRIMARY_SHADER_PARAMS.md',
 'Content/TLOU2/Reports/CAPTURE_FG_SOURCE_PRIMARY_SHADER_PARAMS.json','Content/TLOU2/Reports/CAPTURE_FG_SOURCE_PRIMARY_SHADER_PARAMS.md',
 'Content/TLOU2/Reports/CAPTURE_FG_PRIMARY_MATERIAL_CONSTANTS.json',
 runtime_path,'Exports/capture_matched_catalog_map_validation.json','Exports/catalog_controls_validation.json',
 'Exports/captured_corrective_curve_validation.json','Exports/final_material_usage_fix_result.json','Exports/final_material_usage_persistent_validation.json',
 'Exports/original_0fw_ue_transform_validation.json','Exports/original_viewer_ue_transform_validation.json',
 'Exports/owned_rig_integration_report.json','Exports/backpack_variant_replacement_report.json','Exports/capture_hidden_base_arms_report.json',
 'Exports/capture_matched_patrol_manifest.json','Exports/capture_matched_chunk_manifest.json','Exports/captured_skin_pose_chunk_manifest.json',
 'Exports/capture_mesh_precision_report.json','Exports/capture_fg_stage_manifest.json','Exports/capture_fg_stage_validation.json',
 'Exports/import_captured_fg_stage_result.json','Exports/captured_fg_stage_ue_validation.json',
 'Exports/captured_fg_stage_exchange_validation.json',
 'Exports/canonical_gltf_split_validation.json',
 'Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_verification.json',
 'Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_application.json',
 'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json',
 'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_reference_verification.json',
 'Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.json','Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.bin',
 'Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.npz','Exports/CaptureBuffers/Capture_Hoodie_SkinPalette75.json',
 'Exports/CaptureBuffers/Capture_Hoodie_SkinPalette75.npz','Exports/CaptureBuffers/shader_index.json',
 'Exports/Ellie_CorrectBindRest_SourceMatrices.json','Exports/Ellie_AugmentedBindRest_SourceMatrices.json',
 'Exports/Ellie_Patrol_CapturedSkinPose_validation.json','Exports/Ellie_Patrol_Original_0FW_blender_validation.json',
 'Exports/Ellie16_Patrol_OriginalViewerPose_blender_validation.json','Exports/TexturesDecoded/texture_decode_manifest.json',
 'Exports/reconstructed_eye_material_report.json','Exports/Ellie_Patrol_Original0FW_AnimationPreview_report.json',
 'Exports/Ellie_Patrol_CapturedSkinPose_Preview_report.json',
 'Exports/Ellie_Patrol_NeutralModel_Preview_report.json',
]
canonical={}
def add(rel,role,required=False):
    path=ROOT/rel if not Path(rel).is_absolute() else Path(rel)
    try:key=relpath(path)
    except ValueError:return
    if key not in canonical:canonical[key]={'path':key,'role':role,'required':required,'exists':path.exists()}
    elif required:canonical[key]['required']=True
for model in MODELS:
    for kind in ['blend','fbx','glb','gltf','bin']:add(model[kind],model['label']+' '+kind,True)
    add('Exports/'+model['stem']+'_gltf_skin_validation.json',model['label']+'全12路glTF蒙皮权重验证')
for row in trajectories:add(row['path'],'原始/截帧零位移RootMotion轨迹CSV',True)
for row in root_motion.get('files',[]):add(row['csv'],'原始游戏坐标完整RootMotion T/Q/S与增量CSV',True)
for row in previews:add(row['path'],row['label'],True)
add('TLOU2Codex.uproject','UE5.8工程入口',True)
add('Content/TLOU2/Maps/ElliePatrolCaptureMatched.umap','目标图鉴地图',True)
for rel in ['Open_Catalog_UE58.cmd','Play_Catalog_UE58.cmd','Binaries/Win64/UnrealEditor-TLOU2Codex.dll',
            'Binaries/Win64/UnrealEditor.modules','Binaries/Win64/TLOU2CodexEditor.target']:
    add(rel,'UE5.8启动脚本或已编译运行时',True)
add('Scripts/verify_final_delivery_integrity.py','规范交付文件完整性核验脚本',True)
for rel in EVIDENCE:add(rel,'验证与来源证据')
for pattern in ['Config/*.ini','Source/**/*.h','Source/**/*.cpp','Source/**/*.cs']:
    for path in ROOT.glob(pattern):add(relpath(path),'UE运行时代码或工程配置')
for folder in ['Content/TLOU2/CaptureMatched1152','Content/TLOU2/TexturesDecoded']:
    for path in (ROOT/folder).rglob('*.uasset'):add(relpath(path),'当前UE角色/动画/材质/贴图资产')
for row in material.get('materials',[]):
    package=row.get('ue_material_path','').split('.')[0]
    if package.startswith('/Game/'):add('Content/'+package[6:]+'.uasset','最终24个角色材质')
for rel in ['Content/TLOU2/Reference/T_CatalogInstructionBar.uasset']:
    add(rel,'运行时HUD指令栏')
for path in (ROOT/'Exports/TexturesDecoded').glob('*.png'):add(relpath(path),'原始解码PNG或明确标注的派生材质图')
for path in (ROOT/'Exports/MaterialPortability').glob('*.json'):add(relpath(path),'四个Blender文件的打包与动作签名')
for path in (ROOT/'Exports/CaptureBuffers/Shaders').glob('*'):
    if path.is_file():add(relpath(path),'原始DXBC/DXIL或对应反汇编')
for path in (REPORTS/'ShaderEvidence').glob('*.bin'):add(relpath(path),'材质原始捕获CBV字节')
for path in (ROOT/'Scripts/ExporterSupport/OriginalBlenderGLTF_5_2').glob('*.py'):add(relpath(path),'Blender5.2原始导出器备份与可复现修改依据')
numeric_references=read('Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json')
for row in numeric_references.get('rows',[]):
    for key in ['path','source_npz','source_capture']:
        if row.get(key):add(row[key],'最终29网格原始属性与独立蒙皮数值参考',True)
for key in ['source_format_evidence','original_shader_weight_evidence','capture_selection_evidence']:
    if numeric_references.get(key):add(numeric_references[key],'原始蒙皮存储格式/权重shader/实际捕获归属证据',True)
for item in material.get('source_paks',[]):add('Content/TLOU2/SourcePaks/'+item['pak'],'最终29网格原始PAK')
for rel in ['Content/TLOU2/SourcePaks/ellie-skel.pak','Content/TLOU2/SourcePaks/Animations/anim-ellie-player-movement.pak',
            'Content/TLOU2/SourcePaks/Animations/anim-ellie-player-bindpose.pak']:
    add(rel,'原始骨架/动画PAK')
for stem in ['ellie-prone-lg-aim-strafe-0-fw','model-viewer-ellie-16-patrol']:
    for suffix in ['.json','.csv','.ndanim.bin','_RootTrajectory.csv']:
        candidate='Exports/AnimationSources/DecodedOriginal/'+stem+suffix
        if (ROOT/candidate).exists():add(candidate,'原始数值动画与源码二进制')
decode0=read('Exports/AnimationSources/DecodedOriginal/ellie-prone-lg-aim-strafe-0-fw.json')
payload=decode0.get('source',{}).get('source_payload_file')
if payload:add(payload,'0FW原始2496字节codec负载')
if dump_path.exists():
    add(dump_path,'最新UE运行时顶点审计元数据')
    for row in read(relpath(dump_path)).get('meshes',[]):
        if row.get('positions'):add(row['positions'],'最新UE运行时component-local顶点float32')
for value in stage_manifest.get('exports',{}).values():
    if isinstance(value,str):add(value,'原始FG展台交换源')
for rel in stage_manifest.get('canonical_artifacts',[]):add(rel,'原始FG展台资产或验证')
for path in (ROOT/'Exports/CapturedFGStage/TexturesDecoded').glob('*.png'):add(relpath(path),'原始FG地台解码PNG')
for path in (ROOT/'Exports/CapturedFGStage/TexturesDerived').glob('*'):
    if path.is_file():add(relpath(path),'原始shader参数派生的可移植主层贴图')
for path in (ROOT/'Exports/FGPrimaryMaterialPort').glob('*.json'):add(relpath(path),'五份Blender地台主层材质签名与来源')
for row in read('Exports/CapturedFGStage/captured_fg_stage_manifest.json').get('rows',[]):
    for key in ['source_npz','posed_npz','world_posed_npz']:
        if row.get(key):add(row[key],'FG原始属性缓冲/截帧蒙皮/实例世界矩阵证据')
# Save only the current map's authoritative stage assets, never old stage folders.
for row in read('Exports/capture_matched_catalog_map_result.json').get('stage',[]):
    if row.get('mesh'):
        package=row['mesh'].split('.')[0]
        if package.startswith('/Game/'):add('Content/'+package[6:]+'.uasset','当前地图展台静态网格')

LIMITS=[
 '未知参考绑定：人类1074节点中520条原始SQT已恢复，554条helper参考仍明确标注为未解析；帽衫另有75条原始SQT与3条helper回退。截帧蒙皮矩阵是独立证据，不将其冒称为原始helper绑定姿态。',
 '截帧是单个静态状态；CaptureAffineCorrective只补偿该状态中骨骼TRS无法表达的仿射剪切。原始0FW/图鉴姿态不使用这项截帧专用修正。',
 '帽衫20个sim节点保留，但只有本截帧的静态布料矩阵；没有宣称恢复动态布料模拟或为稀疏0FW补造模拟动画。',
 '眼球UV缩放3.2为推定参数；头发使用可移植PBR/遮罩，泪膜使用透明度.08/粗糙度.12；原始纤维光学、角膜折射、皮肤SSS与分层湿润shader没有完整移植。',
 '原始NPZ没有提供独立的顶点法线/切线；Blender拆分法线与导出的body切线属于重建的DCC着色基底，保留它们不代表已逐位恢复原始GPU法线/切线或法线图绿色通道方向。位置、权重与拓扑验证不涵盖该基底。',
 '0FW是26骨骼右臂/手指稀疏动画层，不是整段角色移动；图鉴源为1帧，UE两帧保持仅为兼容零时长导入。两者及截帧姿态的RootMotion位移为零。',
 '实际UE运行时数值验证与外观比对独立于文件存在性；未通过的最新报告保持待完成状态，截图文件本身不构成通过证据。',
]
SUPERSEDED='旧 Exact、1074/1390 骨架、RawRootCandidate、Probe、Proxy、synthetic/root-motion测试与旧组合展台均为历史调试记录，已被本索引取代，不属于规范交付入口。'
metrics={'selected_meshes':29,'allocated_vertices':84954,'triangles':117459,'triangle_referenced_vertices':84362,
         'unreferenced_head_buffer_vertices':592,'captured_glb_export_vertices':gltf.get('export_vertices',84578),
         'game_bones':1152,'human_bones':1074,'hoodie_bones':78,'ue_bones_including_object_root':1153,
         'original_decoded_texture_entries':340,'materials':24,'maximum_influences':12,
         'ue_runtime_render_vertices':runtime.get('ue_render_vertices'),
         '0fw_source_bones':26,'0fw_source_frames':80,'0fw_delivery_rate_hz':30,
         'viewer_source_bones':520,'viewer_source_frames':1,'viewer_ue_hold_samples':2,
         'stage_meshes':33,'stage_vertices':101538,'stage_materials':27,'stage_original_textures':206}
states={'original_source_records':passed(source_validation),'independent_blender_capture_vertices':passed(raw) and raw_fresh,'independent_blender_capture_hash_current':raw_fresh,
        'original_triangle_index_buffers':passed(triangles),'ue_animation_full_float_compression':passed(compression),
        'original_animation_glb_samples':passed(glb_animation) and glb_animation_fresh,'original_animation_glb_hash_current':glb_animation_fresh,
        'captured_gltf_accessor_pose':gltf_pass,'captured_gltf_hash_current':gltf_fresh,
        'neutral_fbx_roundtrip':passed(fbx),'0fw_native_codec':passed(codec),'viewer_native_constants':passed(viewer_native),
        'all_four_glb_skin_data':all(passed(r) for r in skin_reports) and skin_reports_fresh,'all_four_glb_skin_hash_current':skin_reports_fresh,
        'source_fg_primary_shader_persisted':passed(fg_primary) and fg_primary_fresh,'source_fg_primary_shader_hash_current':fg_primary_fresh,
        'source_character_primary_shader_persisted':passed(character_primary),
        'preview_source_and_png_hash_current':previews_fresh,'all_80_source_frame_gif_hash_and_timing':gif_fresh,
        'all_four_fbx_source_fidelity':passed(fbx_all) and fbx_all_fresh,'all_four_fbx_hash_current':fbx_all_fresh,
        'root_motion_game_space_transforms':passed(root_motion) and root_motion_fresh,'root_motion_game_space_hash_current':root_motion_fresh,
        '0fw_ue_local_transforms':passed(ue0),'viewer_ue_local_transforms':passed(ueviewer),
        'ue_map_reload':passed(map_validation),'controls':passed(controls),'capture_morph_persisted':passed(morph),
        'material_usage_persisted':passed(usage),'captured_mesh_defaults_match_scene':mesh_material_sync_fresh,
        'ue_runtime_vertices':runtime_pass,'ue_runtime_report_fresh':runtime_fresh,
        'capture_camera_constants':passed(camera),'original_fg_stage':stage_pass,
        'fg_exchange_roundtrip':passed(stage_exchange) and stage_exchange_fresh,'fg_exchange_hash_current':stage_exchange_fresh}
delivery={'schema':'tlou2.canonical_delivery.v1','generated_utc':NOW,'project_root':str(ROOT),'capture':CAPTURE,
          'ue_editor':EDITOR,'ue_map':MAP,'models':MODELS,'metrics':metrics,'validation':states,
          'runtime_status':runtime_status,'runtime_detail':runtime_detail,'stage_status':stage_status,
          'trajectories':trajectories,'previews':previews,'limitations':LIMITS,'historical_superseded':SUPERSEDED,
          'evidence':EVIDENCE,'items':list(canonical.values())}

def model_table(base):
    lines=['| 用途 | Blender | FBX | glTF / GLB |','|---|---|---|---|']
    for m in MODELS:lines.append('| '+m['label']+' | '+link(m['blend'],'源文件',base)+' | '+link(m['fbx'],'FBX',base)+' | '+link(m['glb'],'GLB',base)+' / '+link(m['gltf'],'glTF JSON + BIN',base)+' |')
    return lines

def index_doc(base):
    lines=['# 艾莉巡逻服装规范交付','',
       '**角色规范版本：29 网格 / 84,954 分配顶点 / 117,459 三角形 / 1,152 骨骼。** UE运行时：'+runtime_status+'；原始FG展台：'+stage_status+'。',
       runtime_detail,'',
       '用 '+link('TLOU2Codex.uproject','TLOU2Codex.uproject',base)+' 在 `'+EDITOR+'` 打开工程，加载 `'+MAP+'` 后运行。场景使用真实3D角色、展台与HUD；原始截帧仅作参考证据。','']
    lines+=['快捷启动：'+link('Open_Catalog_UE58.cmd','打开编辑器',base)+' / '+link('Play_Catalog_UE58.cmd','直接运行图鉴',base)+'。工程已包含匹配UE5.8的运行时模块。','']
    lines+=model_table(base)
    lines+=['','绑定与动画说明：中性文件用于原始A形参考绑定编辑；截帧文件用于静态图鉴复刻；原始图鉴与0FW动画保持各自数值来源。1,074人类节点+78帽衫节点组成规范骨架，UE另含1个导出对象根节点。Blender源文件为5.2格式，请使用Blender5.2或更新版本。','',
       '84,954为原始顶点缓冲分配数，其中592个头部位置没有被三角索引引用；可绘制参考为84,362。截帧GLB有'+str(metrics['captured_glb_export_vertices'])+'个顶点，含UV/属性边界的拆分或合并，不要求与原始缓冲分配数相同。','',
       '117,459个原始三角形的29份有序索引缓冲已在444次实际DrawIndexed中逐位匹配。FG地台另含33网格、101,538分配顶点、27材质与206条原始解码贴图；已使用其独立16节点蒙皮与实际图形实例矩阵，世界坐标烘焙后以单位变换导入。','',
       '地台独立交换文件：'+link('Blender/Catalog_CapturedFGStage.blend','Blender',base)+' / '+link('Exports/Catalog_CapturedFGStage.fbx','FBX',base)+' / '+link('Exports/Catalog_CapturedFGStage.glb','GLB',base)+'。FBX与GLB往返均保留124,086三角形及其绕序/重复次数。JSON glTF与同名BIN须一同保留。','',
       '## 轨迹、贴图与预览','']
    for row in trajectories:lines.append('- '+link(row['path'],Path(row['path']).name,base)+'：'+str(row.get('samples',0))+'样本，最大根位移 '+number(row.get('maximum_displacement_m'))+' m。')
    for row in root_motion.get('files',[]):lines.append('- '+link(row['csv'],Path(row['csv']).name,base)+'：游戏坐标Y-up完整T/Q/S与相对首帧增量，'+str(row['frames'])+'样本，根位移和旋转均为零。')
    lines+=['- 旧 `RootTrajectory.csv` 使用Blender坐标；新增 `RootMotion_GameSpace.csv` 使用原始游戏X右/Y上/Z前坐标。原始命名root靠近骨盆，其参考高度不代表移动；UE导出对象根也保持静止。']
    lines+=['- '+link('Exports/TexturesDecoded/texture_decode_manifest.json','340条原始解码贴图清单',base)+'；PNG位于 `Exports/TexturesDecoded`，派生眼球/法线图片另行标注。']
    for row in previews:lines.append('- '+link(row['path'],row['label'],base)+'：'+row['role']+'。')
    lines+=['','操作：鼠标左键拖动旋转；W/A/S/D平移；Z/X或滚轮缩放；Q/E最近/最远；R复位；F显隐UI；Esc退出。','',
       '## 验证与来源','',
       '- '+link('Content/TLOU2/Reports/VALIDATION_REPORT.md','验证报告',base)+'、'+link('Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.md','材质映射',base)+'。',
       '- '+link('Content/TLOU2/Reports/CAPTURE_MESH_SOURCE_BINDING_VALIDATION.md','原始PAK与GPU记录逐网格匹配',base)+'。原始角色PAK保存在 `Content/TLOU2/SourcePaks`；原始动画数值与负载保存在 `Exports/AnimationSources/DecodedOriginal`。',
       '- '+link('Content/TLOU2/Reports/CAPTURE_SHADER_SKINNING.md','截帧shader与蒙皮分析',base)+'；331个shader与57个根签名容器/反汇编位于 `Exports/CaptureBuffers/Shaders`。',
       '- '+link('Content/TLOU2/Reports/CAPTURE_ORIGINAL_CAMERA_CONSTANTS.md','原始相机证据',base)+'：game Y-up位置(0,1.15,3)m，水平FOV79.9908974°；UE位置(0,300,115)cm，俯角10.431785°。',
       '- '+link('Content/TLOU2/Reports/CAPTURE_FG_STAGE_VALIDATION.md','原始FG地台与遮罩证据',base)+'；蕨叶与苔藓使用源深度预通道独立R遮罩，UE保留原始距离阈值公式。地面多层材质仍为PBR近似。',
       '- '+link('Content/TLOU2/Reports/FINAL_DELIVERY_MANIFEST.json','规范文件SHA-256清单',base)+'；仅涵盖规范资产，不包含多GB截帧页缓存/历史试验。','',
       '## 范围与限制','']
    lines+=['- '+s for s in LIMITS]
    lines+=['',SUPERSEDED,'']
    return '\n'.join(lines)

native=codec.get('native_comparison',{})
validation=['# 最终规范验证报告','',
 '生成时间（UTC）：'+NOW+'。本文件读取现有证据，未启动UE或Blender。**UE运行时：'+runtime_status+'。** '+runtime_detail,
 '原始FG展台：'+stage_status+'。','',
 '| 检查 | 当前结果 | 主要证据 |','|---|---|---|']
tests=[('最终29网格原始GPU权重/绑定',states['original_source_records'],'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_reference_verification.json'),
       ('117459原始三角形实际DrawIndexed逐位索引匹配',states['original_triangle_index_buffers'],'Content/TLOU2/Reports/CAPTURE_CHARACTER_TRIANGLE_INDEX_VALIDATION.json'),
       ('Blender截帧84954顶点独立对比',states['independent_blender_capture_vertices'],'Exports/captured_pose_independent_raw_vertex_validation.json'),
       ('GLB独立访问器/绑定/形变对比，且文件哈希匹配',states['captured_gltf_accessor_pose'],'Exports/captured_gltf_independent_pose_validation.json'),
       ('中性FBX重新导入',states['neutral_fbx_roundtrip'],'Exports/neutral_fbx_roundtrip_validation.json'),
       ('四份GLB全部12路蒙皮权重/绑定闭合且哈希匹配',states['all_four_glb_skin_data'],'Exports/Ellie_Patrol_Catalog_CaptureMatched_gltf_skin_validation.json'),
       ('四份FBX实际二进制117459三角形/源权重及绑定，文件哈希匹配',states['all_four_fbx_source_fidelity'],'Exports/canonical_fbx_fidelity_validation.json'),
       ('游戏坐标完整RootMotion T/Q/S与增量、文件哈希匹配',states['root_motion_game_space_transforms'],'Exports/final_root_motion_transform_validation.json'),
       ('0FW原始codec/native核验',states['0fw_native_codec'],'Content/TLOU2/Reports/TARGET_0FW_COMPLETE_DECODE_VALIDATION.json'),
       ('图鉴原始常量核验',states['viewer_native_constants'],'Content/TLOU2/Reports/MODEL_VIEWER_NATIVE_CONSTANT_VERIFICATION.json'),
       ('0FW UE逐帧局部变换',states['0fw_ue_local_transforms'],'Exports/original_0fw_ue_transform_validation.json'),
       ('图鉴UE两帧保持局部变换',states['viewer_ue_local_transforms'],'Exports/original_viewer_ue_transform_validation.json'),
       ('原始动画GLB全部骨骼/源帧SQT且文件哈希匹配',states['original_animation_glb_samples'],'Exports/original_animation_glb_sample_validation.json'),
       ('三份UE动画重启后RAW/COMPRESSED全骨骼逐帧',states['ue_animation_full_float_compression'],'Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_verification.json'),
       ('UE地图重新加载',states['ue_map_reload'],'Exports/capture_matched_catalog_map_validation.json'),
       ('图鉴控制8项',states['controls'],'Exports/catalog_controls_validation.json'),
       ('截帧修正形变持久化',states['capture_morph_persisted'],'Exports/captured_corrective_curve_validation.json'),
       ('骨骼/Morph材质使用标记持久化',states['material_usage_persisted'],'Exports/final_material_usage_persistent_validation.json'),
       ('CapturedMeshes默认材质与场景实例逐槽一致（5资产/24槽）',states['captured_mesh_defaults_match_scene'],'Exports/captured_mesh_scene_material_sync_validation.json'),
       ('地台原始主层参数/颜色转换/湿润方程持久化',states['source_fg_primary_shader_persisted'],'Exports/source_fg_primary_ue_validation.json'),
       ('外套/裤子原始主层贴图/颜色转换/法线/AO持久化',states['source_character_primary_shader_persisted'],'Exports/source_character_material_ue_persistence_verify.json'),
       ('最新实际UE运行时顶点/相机/形变',runtime_pass,runtime_path),
       ('最终源文件PNG预览哈希与FG33场景',states['preview_source_and_png_hash_current'],'Exports/Ellie_Patrol_CapturedSkinPose_Preview_report.json'),
       ('80帧原始动画GIF哈希与2670ms时间',states['all_80_source_frame_gif_hash_and_timing'],'Exports/Ellie_Patrol_Original0FW_AnimationPreview_report.json'),
       ('原始FG33展台与UE保存持久化',states['original_fg_stage'],'Exports/captured_fg_stage_ue_validation.json')]
tests.append(('FG的FBX/GLB独立重导入、世界坐标与124086三角形',states['fg_exchange_roundtrip'],'Exports/captured_fg_stage_exchange_validation.json'))
for title,ok,evidence in tests:validation.append('| '+title+' | '+('通过' if ok else '待完成 / 未通过')+' | '+link(evidence,Path(evidence).name,REPORTS)+' |')
validation+=['','## 数值范围','',
 f"Blender独立最大位置误差：{number(raw.get('maximum_error_m'))} m；GLB可绘制表面最大双向误差：{number(gltf.get('normalized_bidirectional_max_m'))} m；UE实际运行时最大误差：{number(runtime.get('bidirectional_max_distance_m'))} m。这些检查的空间、顶点覆盖和容差分别以对应JSON为准。",
 f"0FW为26骨骼、80帧、30Hz：native unpack/range各{native.get('unpack_frames_bit_exact','?')}/{native.get('range_frames_bit_exact','?')}帧逐位一致；动态float4四元数{native.get('quaternion_float4_bit_exact','?')}/{native.get('quaternions_compared','?')}逐位一致。常量Quat48仍保留与native近似SIMD平方根的舍入范围，不将这项误差抹平。",
 '原始图鉴为520骨骼、1帧；原始浮点向量/标量位级匹配，Quat48与native近似平方根存在约1e-7量级舍入差。UE保持载体仅复制为2个相同样本。',
    'UE动画采用独立LeastDestructive全浮点压缩设置；重启后比较全部1153骨骼、0FW全部80帧及两份保持载体的每帧。RAW/COMPRESSED最大全局平移差 '+number(compression.get('maximum_raw_compressed_global_translation_error_cm'),10)+' mm。旋转W重建仍有明确浮点舍入，详见逐帧报告。',
    '三份RootTrajectory CSV记录Blender坐标参考根变换；新增三份RootMotion_GameSpace CSV记录原始游戏坐标完整T/Q/S与增量。原始命名root靠近骨盆，参考位置不是移动；全部根位移和旋转为零，不混入旧raw-root候选或合成移动。0FW是右臂/手指稀疏层，不能据其命名宣称已恢复全身移动。','',
 '## 材质与可移植性','',
    '24/24材质绑定、340条原始PNG与解码SHA-256一致。四个Blender文件的活动图片已打包；GLB图片内嵌；角色FBX请保留 `Exports/TexturesDecoded`，独立FG地台FBX请保留整个 `Exports/CapturedFGStage` 子目录（含 `TexturesDecoded` 与 `TexturesDerived`）。各文件的精确打包数量见 `Exports/MaterialPortability`。原始PAK、shader字节及相机绑定证据独立保留。',
 link('Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.md','材质近似与逐项映射',REPORTS)+'。','',
 '## 保留限制','']
validation+=['- '+s for s in LIMITS]
validation+=['',SUPERSEDED,'']

(ROOT/'README.md').write_text(index_doc(ROOT),encoding='utf-8')
(REPORTS/'DELIVERY_INDEX.md').write_text(index_doc(REPORTS),encoding='utf-8')
(REPORTS/'交付说明_艾莉巡逻服装.md').write_text(index_doc(REPORTS),encoding='utf-8')
(REPORTS/'VALIDATION_REPORT.md').write_text('\n'.join(validation),encoding='utf-8')
(REPORTS/'DELIVERY_INDEX.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf-8')
for rel in ['README.md','Content/TLOU2/Reports/DELIVERY_INDEX.md','Content/TLOU2/Reports/交付说明_艾莉巡逻服装.md',
            'Content/TLOU2/Reports/VALIDATION_REPORT.md','Content/TLOU2/Reports/DELIVERY_INDEX.json','Scripts/write_canonical_delivery_report.py']:
    add(rel,'规范交付文档或生成器',True)
manifest_rows=[]
for rel,row in sorted(canonical.items()):
    path=ROOT/rel
    item=dict(row)
    if path.exists() and path.is_file():
        before=path.stat();item.update({'bytes':before.st_size,'sha256':hash_file(path),'mtime_utc':datetime.fromtimestamp(before.st_mtime,timezone.utc).isoformat()})
        after=path.stat();item['stable_during_hash']=before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
    manifest_rows.append(item)
manifest={'schema':'tlou2.canonical_file_manifest.v1','generated_utc':NOW,'selection':metrics,'validation':states,
          'policy':'Explicit canonical allowlist only; excludes original multiGBcapture, CaptureBuffers/Chunks caches, Saved/Intermediate/DDC, historical Exact1074/1390/RawRoot/Probe/Proxy/synthetic experiments. Manifest itself is excluded from its self hash.',
          'canonical_file_count':sum(r['exists'] for r in manifest_rows),'canonical_total_bytes':sum(r.get('bytes',0) for r in manifest_rows),
          'missing_required':[r['path'] for r in manifest_rows if r['required'] and not r['exists']],
          'unstable_files':[r['path'] for r in manifest_rows if r.get('stable_during_hash') is False],
          'items':manifest_rows}
(REPORTS/'FINAL_DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'canonical_models':len(MODELS),'runtime_pass':runtime_pass,'runtime_fresh':runtime_fresh,'stage_pass':stage_pass,
                  'manifest_files':manifest['canonical_file_count'],'manifest_bytes':manifest['canonical_total_bytes'],
                  'missing_required':manifest['missing_required'],'unstable_files':manifest['unstable_files']},ensure_ascii=False))
