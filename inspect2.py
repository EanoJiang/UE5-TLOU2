import unreal
for c in [unreal.CanvasPanel,unreal.WidgetTree,unreal.Border,unreal.Image,unreal.Widget,unreal.CanvasPanelSlot,unreal.Margin,unreal.Anchors,unreal.WidgetBlueprintFactory]:
    unreal.log(str(c)+" "+str([x for x in dir(c) if not x.startswith("_")]))
