import sys, unreal
sys.path.append(r"D:/EpicGame/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python")
from editor_toolset.toolsets.blueprint import BlueprintTools
bp=BlueprintTools.create("/Game/Test", "HUDTest2", unreal.HUD.static_class())
g=BlueprintTools.get_graph(bp,"EventGraph")
e=BlueprintTools.add_event(bp,"ReceiveDrawHUD",unreal.IntPoint(0,0))
n=BlueprintTools.create_node(g,"Painting|DrawText",unreal.IntPoint(400,0))
unreal.log("NODE="+str(n))
info=BlueprintTools._get_node_info(n)
unreal.log("PINS="+str(info))
for p in info.input_pins: unreal.log("IN "+str(p))
for p in info.output_pins: unreal.log("OUT "+str(p))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
