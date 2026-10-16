import unreal
bp=unreal.load_asset("/Game/TestW2")
gc=bp.generated_class()
for obj,name in [(gc,"gc"),(unreal.get_default_object(gc),"cdo")]:
    unreal.log(name+" "+str([x for x in dir(obj) if "tree" in x.lower() or "widget" in x.lower()]))
    for prop in ["widget_tree","WidgetTree"]:
        try: unreal.log(name+" "+prop+" "+str(obj.get_editor_property(prop)))
        except Exception as e: unreal.log(name+" "+prop+" ERR "+str(e))
