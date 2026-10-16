"""Preserve imported source tracks in the final UE runtime animations.

The default ACL threshold of0.01 is applied in child local units; FBX retains
the meter-to-cm factor100 on the synthetic armature root. This previously erased
sub-centimeter helper translations. LeastDestructive preserves source floats.
"""
import unreal,json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
settingpath='/Game/TLOU2/CaptureMatched1152/Settings/CaptureBoneFullFloat'
settings=unreal.load_asset(settingpath)
if not settings:
    settings=unreal.EditorAssetLibrary.duplicate_asset('/Game/TLOU2/Diagnostics/CaptureBoneFullFloat',settingpath)
assert isinstance(settings,unreal.AnimBoneCompressionSettings)
codecs=list(settings.get_editor_property('codecs'))
assert len(codecs)==1 and codecs[0].get_class().get_name()=='AnimCompress_LeastDestructive'
settings.set_editor_property('error_threshold',0.)
settings.set_editor_property('force_below_threshold',True)
unreal.EditorAssetLibrary.save_loaded_asset(settings)
rows=[]
for path in unreal.EditorAssetLibrary.list_assets('/Game/TLOU2/CaptureMatched1152/Animations',recursive=True,include_folder=False):
    asset=unreal.load_asset(path)
    if not isinstance(asset,unreal.AnimSequence):continue
    before=asset.get_editor_property('bone_compression_settings').get_path_name()
    asset.set_editor_property('allow_frame_stripping',False)
    asset.set_editor_property('do_not_override_compression',True)
    unreal.AnimationLibrary.set_bone_compression_settings(asset,settings)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset),path
    rows.append({'asset':asset.get_path_name(),'previous_settings':before,
        'settings':settings.get_path_name(),'allow_frame_stripping':False,
        'do_not_override_compression':True,'play_length_seconds':float(asset.get_play_length())})
assert len(rows)>=3,len(rows)
report={'compression_settings':settings.get_path_name(),'codec':'AnimCompress_LeastDestructive',
    'animations':rows,'asset_count':len(rows),
    'source_track_policy':'Imported source curves and bone tracks untouched; only runtime compression settings updated.',
    'required_verification':'Restart UE to rebuild/load derived compression data, then compare compressed pose and RHI/runtime vertices. Same-process evaluation may retain old compressed bytes.',
    'isolated_verification':'Exports/BoneDeformationDiagnostic/reloaded_compression_test.json: maximumRAW-COMPRESSED global translationerror drops1.089047697cm ->0.000116134354cm.'}
(ROOT/'Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_application.json').write_text(json.dumps(report,indent=2))
unreal.log('SOURCE_FIDELITY_COMPRESSION_APPLIED '+json.dumps(report))
