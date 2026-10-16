import unreal
u=unreal.FbxImportUI(); print('FBXUI', [x for x in dir(u) if not x.startswith('_')]); print('props',[x for x in dir(u) if 'skelet' in x.lower() or 'skeleton' in x.lower() or 'import' in x.lower()]); print('SKELDATA', [x for x in dir(u.get_editor_property('skeletal_mesh_import_data')) if not x.startswith('_')]);
