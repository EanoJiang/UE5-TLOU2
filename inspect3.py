import unreal
at=unreal.AssetToolsHelpers.get_asset_tools()
fac=unreal.WidgetBlueprintFactory()
bp=at.create_asset("TestW", "/Game", unreal.WidgetBlueprint, fac)
unreal.log(str(bp))
tree=bp.get_editor_property("widget_tree")
unreal.log(str(tree))
unreal.log(str([x for x in dir(tree) if not x.startswith("_")]))
