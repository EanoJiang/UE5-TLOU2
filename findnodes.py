import sys,unreal
sys.path.append(r"D:/EpicGame/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python")
from editor_toolset.toolsets.blueprint import BlueprintTools
bp=BlueprintTools.create("/Game/Test", "NodeFind", unreal.HUD.static_class())
g=BlueprintTools.get_graph(bp,"EventGraph")
for q in ["Canvas","DrawText","DrawRect","DrawMaterial","GetCanvas","SizeX","PaintContext"]:
    arr=BlueprintTools.find_node_types(g,q)
    unreal.log(q+" => "+str(arr[:120]))
