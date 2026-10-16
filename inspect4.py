import unreal
at=unreal.AssetToolsHelpers.get_asset_tools()
fac=unreal.WidgetBlueprintFactory()
bp=at.create_asset("TestW2", "/Game", unreal.WidgetBlueprint, fac)
for name in ["widget_tree","WidgetTree","get_widget_tree","root_widget"]:
    try: unreal.log(name+" -> "+str(getattr(bp,name)))
    except Exception as e: unreal.log(name+" ERR "+str(e))
try: unreal.log("cdo "+str(unreal.get_default_object(bp.generated_class())))
except Exception as e: unreal.log("cdo err "+str(e))
