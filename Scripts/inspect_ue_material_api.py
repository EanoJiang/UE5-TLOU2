import unreal
unreal.log('MEL '+str([x for x in dir(unreal.MaterialEditingLibrary) if 'expression' in x.lower() or 'material' in x.lower() or 'node' in x.lower()]))
