import unreal
u=unreal.FbxImportUI()
for x in dir(u):
 if not x.startswith('_') and any(k in x.lower() for k in ('skelet','import','mesh','anim')):
  try:
   unreal.log('PROP '+x+'='+str(u.get_editor_property(x)))
  except Exception as e: unreal.log('PROPERR '+x+' '+str(e))
unreal.log('SKELDATA '+str([x for x in dir(u.get_editor_property('skeletal_mesh_import_data')) if not x.startswith('_')]))
unreal.log('INSPECT_DONE')
