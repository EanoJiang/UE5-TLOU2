import unreal
for path in ["/MoverExamples/Characters/Mannequins/Meshes/SK_Mannequin","/MoverExamples/Characters/Mannequins/Animations/Manny/MM_Idle","/MoverExamples/Characters/Mannequins/Animations/Manny/MM_Walk_Fwd","/Engine/BasicShapes/Cube","/Engine/EngineFonts/Roboto"]:
 a=unreal.load_asset(path)
 unreal.log(path+" => "+str(a)+" class="+(a.get_class().get_name() if a else "None"))
