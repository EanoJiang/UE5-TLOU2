import json,re
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
for b in D['bones']:
 n=b['name']
 if re.search(r'(arm|hand|clav|should|thigh|calf|foot|toe|upperarm|forearm|wrist|head|neck|pelvis|root|spine)',n): print(b['index'],n,b['parentIndex'],[round(x,4) for x in b['matrix'][3][:3]])
