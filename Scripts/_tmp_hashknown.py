def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
for s in ['ANIM','ANIM_GROUP','ANIM_RAWCHANNELS','JOINT_HIERARCHY','SKELETON_FLIPDATA','SKELETON','root','transform','rotation','translation','scale','channel','codec','raw','joint','bone','5abe1b4c','41430102']:
 print(s,hex(f(s)))
