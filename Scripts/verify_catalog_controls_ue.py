import json
from pathlib import Path
import unreal

ROOT=Path(r"D:/TLOU2_UE5_8_Codex")
cls=unreal.load_class(None,"/Script/TLOU2Codex.CatalogPawn")
assert cls is not None,"Catalog runtime pawn is missing"
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pawn=actors.spawn_actor_from_class(cls,unreal.Vector(0,0,0))
checks={}
try:
    pawn.reset_catalog_view()
    initial=pawn.get_catalog_camera_location()
    initial_radius=pawn.get_catalog_radius()
    pawn.orbit_catalog_view(45,10)
    orbit=pawn.get_catalog_camera_location()
    checks['orbit_changes_view_without_changing_distance']=((orbit-initial).length()>1 and abs(pawn.get_catalog_radius()-initial_radius)<1e-4)
    before=pawn.get_catalog_pivot()
    pawn.pan_catalog_view(10,5)
    checks['pan_changes_pivot']=(pawn.get_catalog_pivot()-before).length()>1
    pawn.zoom_catalog_view(-100)
    checks['zoom_min_clamped']=abs(pawn.get_catalog_radius()-70)<1e-4
    pawn.zoom_catalog_view(100)
    checks['zoom_max_clamped']=abs(pawn.get_catalog_radius()-800)<1e-4
    pawn.toggle_catalog_menu()
    checks['menu_hides']=not pawn.is_catalog_menu_visible()
    pawn.toggle_catalog_menu()
    checks['menu_restores']=pawn.is_catalog_menu_visible()
    pawn.reset_catalog_view()
    checks['reset_restores_original_camera']=(pawn.get_catalog_camera_location()-initial).length()<1e-4
    checks['reset_restores_original_radius']=abs(pawn.get_catalog_radius()-initial_radius)<1e-4
finally:
    actors.destroy_actor(pawn)
report={'checks':checks,'pass':all(checks.values())}
(ROOT/'Exports/catalog_controls_validation.json').write_text(json.dumps(report,indent=2))
assert report['pass'],str(report)
unreal.log('CATALOG_CONTROLS_VERIFY '+json.dumps(report))
