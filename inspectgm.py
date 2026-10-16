import unreal
gm=unreal.GameModeBase.static_class()
obj=unreal.get_default_object(gm)
unreal.log(str([x for x in dir(obj) if "hud" in x.lower() or "pawn" in x.lower() or "player" in x.lower()]))
