import sys,unreal
sys.path.append(r"D:/EpicGame/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python")
from editor_toolset.toolsets.blueprint import BlueprintTools
bp=BlueprintTools.create("/Game/Test", "HUDTest3", unreal.HUD.static_class())
g=BlueprintTools.get_graph(bp,"EventGraph")
e=BlueprintTools.add_event(bp,"ReceiveDrawHUD",unreal.IntPoint(0,0))
i=BlueprintTools._get_node_info(e)
unreal.log(str(i))
for p in i.input_pins: unreal.log("IN "+str(p))
for p in i.output_pins: unreal.log("OUT "+str(p))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
