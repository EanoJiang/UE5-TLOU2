def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
for s in ['name','joint','value','parent','type','transform','matrix','translation','rotation','scale','position','hash','index','data','channel','bone','id','source','target','joint_name','joint_parent','joint_transform']:
 print(s,hex(f(s)))
