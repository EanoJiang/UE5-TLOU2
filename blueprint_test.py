import sys, unreal
sys.path.append(r"D:/EpicGame/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python")
from editor_toolset.toolsets.blueprint import BlueprintTools
bp=BlueprintTools.create("/Game/Test", "HUDTest", unreal.HUD.static_class())
unreal.log("BP="+str(bp))
g=BlueprintTools.get_graph(bp,"EventGraph")
unreal.log("events="+str(BlueprintTools.list_events(bp)))
e=BlueprintTools.add_event(bp,"ReceiveDrawHUD",unreal.IntPoint(0,0))
unreal.log("event="+str(e))
nodes=BlueprintTools.find_node_types(g,"Draw")
unreal.log("nodes="+str(nodes[:80]))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(bp)
