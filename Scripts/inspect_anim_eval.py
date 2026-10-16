import unreal,json
names=[x for x in dir(unreal) if 'Evaluation' in x or 'AnimPose' in x or 'Frame' in x and 'Anim' in x]
out={'names':names}
for n in names:
 c=getattr(unreal,n)
 try:out[n]=[x for x in dir(c) if not x.startswith('_')]
 except Exception as e:out[n]=repr(e)
open('D:/TLOU2_UE5_8_Codex/Exports/anim_eval_options.json','w').write(json.dumps(out,indent=2,default=str));print(json.dumps(out,indent=2,default=str))
