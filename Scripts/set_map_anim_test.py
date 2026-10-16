import unreal,json,traceback
MAP='/Game/TLOU2/Maps/ElliePatrolChunkedSkeletalRawRootCandidate'; ANIM='/Game/TLOU2/RawRootCandidates/ProbeMesh/Ellie_RawRootCandidate_ellie_prone_lg_aim_strafe_0_fw_Probe_Anim'; anim=unreal.load_asset(ANIM); unreal.EditorLevelLibrary.load_level(MAP); out=[]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
 if isinstance(a,unreal.SkeletalMeshActor) and 'RawRootCandidate_Ellie' in a.get_actor_label():
  c=a.skeletal_mesh_component; d=c.get_editor_property('animation_data'); row={'label':a.get_actor_label(),'before':str(d.get_editor_property('anim_to_play'))}
  try:
   d.set_editor_property('anim_to_play',anim); c.set_editor_property('animation_data',d); c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); c.set_update_animation_in_editor(True); c.set_editor_property('animation_data',d); c.modify(); row['after_mem']=str(c.get_editor_property('animation_data').get_editor_property('anim_to_play'))
  except Exception as e:row['set_err']=repr(e)
  out.append(row)
unreal.EditorLevelLibrary.save_current_level(); open('D:/TLOU2_UE5_8_Codex/Exports/map_anim_set_test.json','w').write(json.dumps(out,indent=2,default=str)); print(json.dumps(out,indent=2,default=str))
