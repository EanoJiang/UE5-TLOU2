import unreal,json,time,re
from pathlib import Path
started=time.monotonic();handle=None
map_path=re.search(r'(/Game/TLOU2/Maps/ElliePatrolCaptureGroom\w*)',unreal.SystemLibrary.get_command_line()).group(1);world_path=map_path+'.'+map_path.rsplit('/',1)[-1]
def tick(dt):
 global handle
 if time.monotonic()-started<3:return
 world=unreal.find_object(None,world_path)
 if world is None:return
 unreal.unregister_slate_post_tick_callback(handle)
 out=[]
 for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
  if 'BP_ElliePatrolCharacter' in a.get_class().get_path_name():
   for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
    m=c.get_editor_property('skeletal_mesh_asset'); row={'name':c.get_name(),'mesh':m.get_path_name() if m else None,'visible':c.is_visible(),'hidden':bool(c.get_editor_property('hidden_in_game')),'parent':c.get_attach_parent().get_name() if c.get_attach_parent() else None,'leader':c.get_editor_property('leader_pose_component').get_name() if c.get_editor_property('leader_pose_component') else None,'anim_mode':str(c.get_editor_property('animation_mode')),'bounds':None}
    try:
     center,extent,r=unreal.SystemLibrary.get_component_bounds(c);row['bounds']={'center':[center.x,center.y,center.z],'extent':[extent.x,extent.y,extent.z]}
    except:pass
    out.append(row)
 Path('D:/TLOU2_UE5_8_Codex/Exports/Groom/HairThinOverlay/runtime_overlay_components_'+world.get_name()+'.json').write_text(json.dumps(out,indent=2),encoding='utf-8');unreal.log('OVERLAY_COMPONENTS '+json.dumps(out))
handle=unreal.register_slate_post_tick_callback(tick)
