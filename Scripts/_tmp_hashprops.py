def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
T={0x52e7fc8056bc65d7,0x68fd26194ecb565a,0xc4bcadba8e631b86,0x8e631b86c4bcadba}
parts=['joint','bone','rotation','translation','scale','transform','position','quaternion','channel','joint_rotation','joint_translation','joint_scale','joint_transform','joint|rotation','joint|translation','joint|scale','joint|transform','rotation_x','rotation_y','rotation_z','rotate','position_x','position_y','position_z','translation_x','translation_y','translation_z','q','t','s','value','values','key','keys']
for x in parts:
 for y in [x,x+'\0',x.upper(),x.lower()]:
  h=f(y)
  if h in T:print(hex(h),repr(y))
  print(repr(y),hex(h))
