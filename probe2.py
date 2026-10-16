import unreal
for path in ["/MoverExamples/Characters/Mannequins/Meshes/SKM_Manny_Simple","/MoverExamples/Characters/Mannequins/Meshes/SK_Mannequin"]:
 a=unreal.load_asset(path)
 unreal.log(path+" => "+str(a)+" class="+(a.get_class().get_name() if a else "None"))
