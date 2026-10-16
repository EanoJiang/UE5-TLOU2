import unreal,json
anim=unreal.load_asset('/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim'); sk=unreal.load_asset('/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe_Skeleton'); out={'class':anim.get_class().get_name() if anim else None}
for prop in ['sequence_length','number_of_frames','num_frames','rate_scale','skeleton','bone_compression_settings','raw_animation_data','track_to_skeleton_map_table','enable_root_motion','root_motion_root_lock','root_motion_translation','root_motion_rotation','additive_anim_type']:
 try: out[prop]=str(anim.get_editor_property(prop))
 except Exception as e: out[prop]='ERR '+str(e)
out['dir']=[x for x in dir(anim) if not x.startswith('_') and any(k in x.lower() for k in ('bone','track','frame','sequence','root','skeleton','transform'))]
try:
 out['bones']=anim.get_editor_property('skeleton').get_reference_pose().get_bone_names(); out['bone_count']=len(out['bones'])
except Exception as e:out['bone_err']=str(e)
for fn,args in [('get_bone_transform',(0,0,0)),('get_bone_transform',(1,0,0)),('get_bone_transform',(0,79,0))]:
 try: out[fn+str(args)]=str(getattr(anim,fn)(*args))
 except Exception as e: out[fn+str(args)]='ERR '+str(e)
open('D:/TLOU2_UE5_8_Codex/Exports/rootmotion_probe_verify.json','w').write(json.dumps(out,indent=2,default=str))
