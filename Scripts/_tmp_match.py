import json,math
# quaternion from row-major rotation matrix? need use scipy? own algorithm
def q_from_m(m):
  # matrix m row basis; standard
  tr=m[0][0]+m[1][1]+m[2][2]
  if tr>0:
   S=math.sqrt(tr+1)*2; w=.25*S; x=(m[2][1]-m[1][2])/S; y=(m[0][2]-m[2][0])/S; z=(m[1][0]-m[0][1])/S
  elif m[0][0]>m[1][1] and m[0][0]>m[2][2]:
   S=math.sqrt(1+m[0][0]-m[1][1]-m[2][2])*2;w=(m[2][1]-m[1][2])/S;x=.25*S;y=(m[0][1]+m[1][0])/S;z=(m[0][2]+m[2][0])/S
  elif m[1][1]>m[2][2]:
   S=math.sqrt(1+m[1][1]-m[0][0]-m[2][2])*2;w=(m[0][2]-m[2][0])/S;x=(m[0][1]+m[1][0])/S;y=.25*S;z=(m[1][2]+m[2][1])/S
  else:
   S=math.sqrt(1+m[2][2]-m[0][0]-m[1][1])*2;w=(m[1][0]-m[0][1])/S;x=(m[0][2]+m[2][0])/S;y=(m[1][2]+m[2][1])/S;z=.25*S
  return (x,y,z,w)
rows=[
('h1', [0.2489013671875,0.438232421875,-0.407958984375,0.7607421875],[0.434326171875,0.92626953125,0.079345703125]),
('h2', [-0.7607421875,-0.407958984375,-0.438232421875,0.2489013671875],[-0.434326171875,0.92626953125,0.079345703125]),
('h3', [-0.0,0.70703125,0.70703125,-0.0],[-0.12353515625,0.0799560546875,-0.0347900390625]),
('h4', [0.0,-0.70703125,0.70703125,-0.0],[0.12353515625,0.0799560546875,-0.0347900390625])]
d=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
# direct local mats from capture; compare q modulo sign and translation
def qdist(a,b): return min(sum((a[i]-b[i])**2 for i in range(4)),sum((a[i]+b[i])**2 for i in range(4)))
for label,q,t in rows:
 matches=[]
 for b in d['bones']:
  m=b['matrix']; q2=q_from_m(m)
  tr=m[3][:3]
  td=sum((tr[i]-t[i])**2 for i in range(3))
  # q basis may need transpose; check both
  q3=q_from_m([[m[j][i] for j in range(3)] for i in range(3)])
  qd=min(qdist(q,q2),qdist(q,q3))
  score=td+qd*100
  matches.append((score,td,qd,b['index'],b['name'],q2,q3,tr))
 print('\n',label,'target',q,t)
 for z in sorted(matches)[:15]:print(z)
