import unreal,json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/BoneDeformationDiagnostic'
doc={}
for label,path in [('base','/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim'),
    ('fullfloat','/Game/TLOU2/Diagnostics/CaptureHold_LeastDestructive')]:
    anim=unreal.load_asset(path)
    settings=anim.get_editor_property('bone_compression_settings')
    info={'path':path,'settings':settings.get_path_name(),'codec_properties':[],'evaluations':{}}
    for c in settings.get_editor_property('codecs'):
        p={'class':c.get_class().get_name()}
        for name in ['ErrorThreshold','TranslationCompressionFormat','RotationCompressionFormat','ScaleCompressionFormat','DefaultVirtualVertexDistance','SafeVirtualVertexDistance']:
            try:p[name]=str(c.get_editor_property(name))
            except Exception as exc:p[name]='ERROR '+str(exc)
        info['codec_properties'].append(p)
    for evalname,kind in [('raw',unreal.AnimDataEvalType.RAW),('compressed',unreal.AnimDataEvalType.COMPRESSED)]:
        opt=unreal.AnimPoseEvaluationOptions()
        opt.set_editor_property('evaluation_type',kind)
        opt.set_editor_property('should_retarget',True)
        opt.set_editor_property('extract_root_motion',False)
        pose=anim.get_anim_pose_at_frame(0,opt)
        def t(t):return {'translation':list(t.translation.to_tuple()),'rotation_xyzw':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],'scale':list(t.scale3d.to_tuple())}
        info['evaluations'][evalname]={str(n):{'local':t(pose.get_bone_pose(n,unreal.AnimPoseSpaces.LOCAL)),
            'global':t(pose.get_bone_pose(n,unreal.AnimPoseSpaces.WORLD))}for n in pose.get_bone_names()}
    doc[label]=info
(OUT/'reloaded_compression_test.json').write_text(json.dumps(doc,indent=2))
unreal.log('RELOADED_COMPRESSION_TEST '+str({k:{a:b for a,b in v.items()if a!='evaluations'}for k,v in doc.items()}))
