import unreal,json
c=unreal.AnimPoseEvaluationOptions(); out={'dir':[x for x in dir(c) if not x.startswith('_')]}
for x in out['dir']:
 try: out[x]=str(c.get_editor_property(x))
 except: pass
open('D:/TLOU2_UE5_8_Codex/Exports/anim_eval_options.json','w').write(json.dumps(out,indent=2))
