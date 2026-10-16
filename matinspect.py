import unreal
unreal.log(str([x for x in dir(unreal.MaterialEditingLibrary) if "expression" in x.lower() or "connect" in x.lower() or "parameter" in x.lower()]))
unreal.log(str([x for x in dir(unreal.Material) if "property" in x.lower() or "blend" in x.lower() or "shading" in x.lower()]))
