import sys,unreal
sys.path.append(r"D:/EpicGame/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python")
from editor_toolset.toolsets.blueprint import BlueprintTools
bp=BlueprintTools.create("/Game/Test", "HUDNodes", unreal.HUD.static_class())
g=BlueprintTools.get_graph(bp,"EventGraph")
for typ in ["HUD|DrawText","HUD|DrawRect","HUD|DrawTextureSimple"]:
 n=BlueprintTools.create_node(g,typ,unreal.IntPoint(100,0))
 unreal.log("TYPE "+typ)
 info=BlueprintTools._get_node_info(n)
 unreal.log(str(info))
 for p in info.input_pins: unreal.log("IN "+str(p))
 for p in info.output_pins: unreal.log("OUT "+str(p))
