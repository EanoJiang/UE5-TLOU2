import unreal, json
u=unreal.FbxImportUI(); d={}
for x in dir(u):
 if not x.startswith('_'):
  try: d[x]=str(u.get_editor_property(x))
  except: pass
open('D:/TLOU2_UE5_8_Codex/Exports/fbxui_props.json','w').write(json.dumps(d,indent=2))
try:
 sd=u.get_editor_property('skeletal_mesh_import_data'); open('D:/TLOU2_UE5_8_Codex/Exports/fbxui_skeletal_props.json','w').write(json.dumps({x:str(sd.get_editor_property(x)) for x in dir(sd) if not x.startswith('_')},indent=2))
except Exception as e: open('D:/TLOU2_UE5_8_Codex/Exports/fbxui_error.txt','w').write(str(e))
