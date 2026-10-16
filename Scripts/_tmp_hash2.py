import json,itertools,re
T=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
def f(s):
 h=0xcbf29ce484222325
 for x in s:h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
names=[x['name'] for x in D['bones']]
base=['root','translation','rotation','scale','quaternion','transform','position','root_motion','rootmotion','pelvis','spinea','spineb','spinec','spined','hips','bone','joint','channel','rawchannels']+names
pre=['','root_','root.','root/','root:','ellie_','ellie.','ellie/','jnt_','bone_','joint_','anim_','channel_']
suf=['','\0','_x','_y','_z','.x','.y','.z','_rotation','_translation','_scale','_quat','_q','_t','_s']
hits=[]
for a in base:
 for p in pre:
  for s in suf:
   for x in [p+a+s,(p+a+s).lower(),(p+a+s).upper()]:
    for enc in ['utf-8','utf-16-le']:
     y=f(x.encode(enc))
     if y in T:hits.append((hex(y),repr(x),enc))
print('hits',len(hits)); print('\n'.join(map(str,hits)))
print('targets',[hex(x) for x in T])
