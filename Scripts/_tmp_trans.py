import json,math
rows=[('h1',[.434326,.926269,.079346]),('h2',[-.434326,.926269,.079346]),('h3',[-.123535,.079956,-.03479]),('h4',[.123535,.079956,-.03479])]
d=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
for nm,t in rows:
 a=[]
 for b in d['bones']:
  tr=b['matrix'][3][:3]; dd=sum((tr[i]-t[i])**2 for i in range(3)); a.append((dd,b['index'],b['name'],tr))
 print(nm)
 for x in sorted(a)[:30]:print(x)
