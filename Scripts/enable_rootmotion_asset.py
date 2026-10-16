import unreal,json
p='/Game/TLOU2/Exact1074/Animations/Ellie_1074_RootMotion_AnimationProbe_Anim'; a=unreal.load_asset(p)
try:
 a.set_editor_property('enable_root_motion',True); a.set_editor_property('root_motion_root_lock',unreal.RootMotionRootLock.REF_POSE); unreal.EditorAssetLibrary.save_asset(p); out={'path':p,'enable_root_motion':str(a.get_editor_property('enable_root_motion')),'root_motion_root_lock':str(a.get_editor_property('root_motion_root_lock')),'sequence_length':str(a.get_editor_property('sequence_length'))}
except Exception as e: out={'error':str(e)}
open('D:/TLOU2_UE5_8_Codex/Exports/rootmotion_enable_result.json','w').write(json.dumps(out,indent=2))
