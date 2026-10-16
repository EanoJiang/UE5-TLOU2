"""Isolate animation compression on a cloned asset; preserve final originals."""
import unreal,json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/BoneDeformationDiagnostic'
basepath='/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim'
base=unreal.load_asset(basepath)
def props(obj,names):
    out={'class':obj.get_class().get_name(),'path':obj.get_path_name()}
    for name in names:
        try:
            value=obj.get_editor_property(name)
            out[name]=value.get_path_name()if isinstance(value,unreal.Object)else str(value)
        except Exception as exc:out[name]='ERROR '+str(exc)
    return out
settings=base.get_editor_property('bone_compression_settings')
report={'base':props(base,['compression_error_threshold_scale','bone_compression_settings','allow_frame_stripping']),
    'base_settings':props(settings,['error_threshold','force_below_threshold']),
    'base_codecs':[props(c,['error_threshold','default_virtual_vertex_distance','safe_virtual_vertex_distance','compression_level','translation_compression_format','rotation_compression_format','scale_compression_format'])for c in settings.get_editor_property('codecs')]}
try:
    tree=base.get_skeleton().get_editor_property('bone_tree')
    report['bone_translation_retargeting_modes']=[str(n.get_editor_property('translation_retargeting_mode'))for n in tree]
except Exception as exc:report['bone_translation_retargeting_modes_error']=str(exc)
(OUT/'original_compression_settings.json').write_text(json.dumps(report,indent=2))
target='/Game/TLOU2/Diagnostics/CaptureHold_LeastDestructive'
clone=unreal.load_asset(target)
if not clone:clone=unreal.EditorAssetLibrary.duplicate_asset(basepath,target)
assert isinstance(clone,unreal.AnimSequence)
settingpath='/Game/TLOU2/Diagnostics/CaptureBoneFullFloat'
precise=unreal.load_asset(settingpath)
if not precise:
    precise=unreal.AssetToolsHelpers.get_asset_tools().create_asset('CaptureBoneFullFloat','/Game/TLOU2/Diagnostics',unreal.AnimBoneCompressionSettings,unreal.AnimBoneCompressionSettingsFactory())
codec_class=unreal.load_class(None,'/Script/Engine.AnimCompress_LeastDestructive')
assert codec_class
codec=unreal.new_object(codec_class,outer=precise,name='FullFloatCodec')
precise.set_editor_property('codecs',[codec])
precise.set_editor_property('error_threshold',0.)
precise.set_editor_property('force_below_threshold',True)
unreal.EditorAssetLibrary.save_loaded_asset(precise)
clone.set_editor_property('allow_frame_stripping',False)
unreal.AnimationLibrary.set_bone_compression_settings(clone,precise)
unreal.EditorAssetLibrary.save_loaded_asset(clone)
report['clone']=props(clone,['compression_error_threshold_scale','bone_compression_settings'])
report['clone_codecs']=[props(c,['translation_compression_format','rotation_compression_format','scale_compression_format'])for c in precise.get_editor_property('codecs')]
def transform(t):return {'translation':list(t.translation.to_tuple()),'rotation_xyzw':[float(t.rotation.x),float(t.rotation.y),float(t.rotation.z),float(t.rotation.w)],'scale':list(t.scale3d.to_tuple())}
report['clone_evaluations']={}
for label,kind in [('raw',unreal.AnimDataEvalType.RAW),('compressed',unreal.AnimDataEvalType.COMPRESSED)]:
    opt=unreal.AnimPoseEvaluationOptions()
    opt.set_editor_property('evaluation_type',kind)
    opt.set_editor_property('should_retarget',True)
    opt.set_editor_property('extract_root_motion',False)
    pose=clone.get_anim_pose_at_frame(0,opt)
    assert pose.is_valid()
    report['clone_evaluations'][label]={str(n):{'local':transform(pose.get_bone_pose(n,unreal.AnimPoseSpaces.LOCAL)),
        'global':transform(pose.get_bone_pose(n,unreal.AnimPoseSpaces.WORLD))}for n in pose.get_bone_names()}
(OUT/'least_destructive_compression_test.json').write_text(json.dumps(report,indent=2))
unreal.log('LEAST_DESTRUCTIVE_CAPTURE_TEST '+str({k:v for k,v in report.items()if k not in('clone_evaluations','bone_translation_retargeting_modes')}))
