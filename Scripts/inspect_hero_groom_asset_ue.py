import unreal,json
for p in ['/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom_HeroCorrected','/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom_HeroCorrected_Grouped']:
 a=unreal.load_asset(p); print(p,type(a).__name__ if a else None)
 if a:
  print([(i.get_editor_property('group_id'),i.get_editor_property('num_curves')) for i in a.get_editor_property('hair_groups_info')])
