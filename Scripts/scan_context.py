import re,sys
p=sys.argv[1];b=open(p,'rb').read()
for needle in [b'SetLeaderPoseComponent', b'SKC_HeadFace', b'SKC_BodyClothing', b'NewLeaderBoneComponent', b'Force Update', b'In Follower Should Tick Pose']:
 print('\n===',needle,'===')
 for m in re.finditer(re.escape(needle),b):
  print('offset',m.start())
  for n in re.finditer(rb'[ -~]{4,}',b[max(0,m.start()-500):m.start()+1000]):
   s=n.group().decode('latin1','replace');
   if len(s)<200: print(' ',max(0,m.start()-500)+n.start(),repr(s))
