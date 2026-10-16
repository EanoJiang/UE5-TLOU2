import unreal
paths=['/Game/TLOU2/Reference/T_CapturedFrame','/Game/TLOU2/Materials/M_CapturedFrame','/Game/TLOU2/Proxy/Ellie_Patrol_Backpack','/Game/TLOU2/Proxy/SK_Ellie_Patrol_Skeleton_Skeleton','/Game/TLOU2/Proxy/Ellie_Patrol_Proxy_Anim']
for p in paths:
 a=unreal.load_asset(p); unreal.log('VERIFY '+p+' => '+str(a)+' class='+(a.get_class().get_name() if a else 'None'))
