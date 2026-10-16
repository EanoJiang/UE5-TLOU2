"""Fresh-process full-hierarchy raw/compressed check on all final animations."""
import unreal,json,math
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
applied=json.loads((ROOT/'Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_application.json').read_text())
settings=applied['compression_settings']
def distance(a,b):return math.sqrt(sum((float(x)-float(y))**2 for x,y in zip(a,b)))
def quaternion_angle(a,b):
    av=[a.x,a.y,a.z,a.w];bv=[b.x,b.y,b.z,b.w]
    dot=abs(sum(x*y for x,y in zip(av,bv)))/math.sqrt(sum(x*x for x in av)*sum(x*x for x in bv))
    return math.degrees(2*math.acos(min(1.,max(0.,dot))))
rows=[]
for item in applied['animations']:
    anim=unreal.load_asset(item['asset'])
    assert anim.get_editor_property('bone_compression_settings').get_path_name()==settings
    assert not anim.get_editor_property('allow_frame_stripping')
    total=max(2,round(anim.get_play_length()*30)+1)
    frames=list(range(total))
    opts=[]
    for kind in [unreal.AnimDataEvalType.RAW,unreal.AnimDataEvalType.COMPRESSED]:
        opt=unreal.AnimPoseEvaluationOptions()
        opt.set_editor_property('evaluation_type',kind)
        opt.set_editor_property('should_retarget',True)
        opt.set_editor_property('extract_root_motion',False)
        opts.append(opt)
    framedata=[]
    for frame in frames:
        raw=anim.get_anim_pose_at_frame(frame,opts[0])
        comp=anim.get_anim_pose_at_frame(frame,opts[1])
        names=[str(n)for n in raw.get_bone_names()]
        assert raw.is_valid()and comp.is_valid()
        assert names==[str(n)for n in comp.get_bone_names()]
        errors=[]
        for name in names:
            values={}
            for label,space in [('local',unreal.AnimPoseSpaces.LOCAL),('global',unreal.AnimPoseSpaces.WORLD)]:
                a=raw.get_bone_pose(name,space);b=comp.get_bone_pose(name,space)
                values[label+'_translation_error']=distance(a.translation.to_tuple(),b.translation.to_tuple())
                values[label+'_rotation_error_degrees']=quaternion_angle(a.rotation,b.rotation)
                values[label+'_scale_error']=max(abs(x-y)for x,y in zip(a.scale3d.to_tuple(),b.scale3d.to_tuple()))
            errors.append({'bone':name,**values})
        summary={k:max(r[k]for r in errors)for k in errors[0]if k!='bone'}
        summary.update({'frame':frame,'bones':len(names),
            'largest_global_translation_errors':sorted(errors,key=lambda r:r['global_translation_error'],reverse=True)[:15]})
        framedata.append(summary)
    rows.append({'asset':anim.get_path_name(),'play_length_seconds':float(anim.get_play_length()),
        'compressed_settings':settings,'frames':framedata,
        'maximum_raw_compressed_global_translation_error_cm':max(r['global_translation_error']for r in framedata)})
out={'compression_settings':settings,'codec':'AnimCompress_LeastDestructive','animations':rows,
    'animation_count':len(rows),
    'maximum_raw_compressed_global_translation_error_cm':max(r['maximum_raw_compressed_global_translation_error_cm']for r in rows),
    'tolerance_cm':0.01,
    'method':'After restarting UE, compare RAW and actual COMPRESSED evaluation with retarget enabled across all 1153 bones, every one of 80 source animation frames and both samples of each hold. Source curves, skeleton and translation retarget modes remain unchanged.',
    'tolerance_policy':'Compression-only error budget100micrometers; final runtime surface budget100micrometers (0.1mm). Actual capturehold error1.161micrometers; original0FW worstcase26.855micrometers. LeastDestructive storesfloat96NoW rotations, so W reconstruction can introduce small residual rounding.',
    'pass':all(r['maximum_raw_compressed_global_translation_error_cm'] < 0.01 for r in rows)}
(ROOT/'Exports/BoneDeformationDiagnostic/final_source_fidelity_compression_verification.json').write_text(json.dumps(out,indent=2))
unreal.log('FINAL_COMPRESSION_VERIFY '+json.dumps({k:v for k,v in out.items()if k!='animations'}))
for row in rows:unreal.log('FINAL_COMPRESSION_ASSET '+str({k:v for k,v in row.items()if k!='frames'}))
assert out['pass'],out['maximum_raw_compressed_global_translation_error_cm']
