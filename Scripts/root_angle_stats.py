import json,math
x=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_f70061_details.json'))[0]['samples']
u=[];offset=0;prev=None
for v in x:
 if prev is not None and v-prev < -3: offset += 2*math.pi
 u.append(v+offset);prev=v
print('n',len(x),'start',u[0],'end',u[-1],'delta',u[-1]-u[0],'meanstep',sum(u[i+1]-u[i] for i in range(len(u)-1))/(len(u)-1),'minmaxstep',min(u[i+1]-u[i] for i in range(len(u)-1)),max(u[i+1]-u[i] for i in range(len(u)-1)), 'duration30',len(x)/30,'duration intervals', (len(x)-1)/30)
print('deg start end delta',*[v*180/math.pi for v in (u[0],u[-1],u[-1]-u[0])])
