import unreal
for c in [unreal.WidgetBlueprint, unreal.WidgetTree, unreal.CanvasPanelSlot, unreal.SlateFontInfo, unreal.TextBlock]:
    print(c, [x for x in dir(c) if not x.startswith("_")][:120])
try: print("SlateFontInfo", unreal.SlateFontInfo("C:/Windows/Fonts/simhei.ttf", 30))
except Exception as e: print("font err",e)
