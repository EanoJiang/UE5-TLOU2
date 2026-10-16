# Catalog controls implementation

The final UE5.8 map will use a small native runtime pawn and HUD. The pawn adopts
the placed catalog camera on BeginPlay, orbits about the character, pans in the
camera plane, clamps zoom, remembers the initial view, and supports reset and
exit. The HUD draws the captured2D instruction strip independently of3D scene
movement. All character and stage geometry remains real3D.

The user authorized autonomous implementation and cannot answer questions.

1. Add a UE commandlet behavioral check for the native pawn. Run it before the
   native class exists and confirm the missing-class assertion fails.
2. Add the project runtime module, editor/game targets, CatalogPawn, CatalogHUD,
   and CatalogGameMode. Build the UE5.8 editor target with installed MSVC.
3. Run the behavioral check: orbit preserves radius, pan shifts pivot, zoom
   clamps both limits, reset restores the initial transform, and menu toggling
   changes HUD visibility. Bind the game mode to the final catalog map.
4. Run the map in game mode and capture the actual rendered viewport. Record
   compiler and runtime checks in a compact validation report.

Key mapping follows the source UI: mouse drag orbit; WASD pan; Z/X zoom;
Q/E zoom limits; R reset; F instructions; Esc exit.
