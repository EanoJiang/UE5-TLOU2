import unreal, json
names=[x for x in dir(unreal) if 'Anim' in x and ('Extract' in x or 'Evaluate' in x or 'Pose' in x)]
out={'names':names}
for n in names:
 try:
  c=getattr(unreal,n); out[n]=str(c)
 except:pass
open('D:/TLOU2_UE5_8_Codex/Exports/anim_python_types.json','w').write(json.dumps(out,indent=2))
