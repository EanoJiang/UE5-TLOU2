import unreal,json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex');src=ROOT/'Scripts/import_capture_groom_ue.py';code=src.read_text(encoding='utf-8');code=code.replace("GROUPED_ABC = OUTPUT / 'Ellie_Patrol_CaptureGroom_Grouped.abc'", "GROUPED_ABC = OUTPUT / 'Ellie_Patrol_CaptureGroom_HeroCorrected.abc'").replace("ABC = GROUPED_ABC if GROUPED_ABC.is_file() else OUTPUT / 'Ellie_Patrol_CaptureGroom.abc'", "ABC = GROUPED_ABC").replace("ASSET_NAME = 'Ellie_Patrol_CaptureGroom'", "ASSET_NAME = 'Ellie_Patrol_CaptureGroom_HeroCorrected'").replace("REPORT = OUTPUT / 'ue_groom_import_result.json'", "REPORT = OUTPUT / 'ue_groom_hero_corrected_import_result.json'").replace("TARGET_MAP = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'", "TARGET_MAP = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'")
ns={'__name__':'hero_corrected_import'};exec(compile(code,str(src),'exec'),ns)
# attach corrected Groom to BP SCS and all four saved preview maps
from editor_toolset.toolsets.actor import ActorTools
from editor_toolset.toolsets.blueprint import BlueprintTools
BP='/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter';GROOM='/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom_HeroCorrected';NAME='Groom_Hair';MAPS=['/Game/TLOU2/Maps/'+n for n in ('ElliePatrolCaptureGroom','ElliePatrolCaptureGroomFront','ElliePatrolCaptureGroomThreeQuarter','ElliePatrolCaptureGroomBack')]
def temps(bp):return {c.get_name().removesuffix('_GEN_VARIABLE'):c for c in ActorTools.get_components(BlueprintTools.get_default_object(bp))}
bp=unreal.load_asset(BP);cs=temps(bp);g=cs[NAME];asset=unreal.load_asset(GROOM);g.set_groom_asset(None);g.set_groom_asset(asset);g.set_editor_property('binding_asset',None);g.set_visibility(True,False);g.set_hidden_in_game(False,False);BlueprintTools.compile_blueprint(bp,warnings_as_errors=True);unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
for mp in MAPS:
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);levels.load_level(mp);chars=[a for a in actors.get_all_level_actors() if a.get_class()==bp.generated_class()];
 if len(chars)==1:
  for c in chars[0].get_components_by_class(unreal.GroomComponent):
   if c.get_name()==NAME:c.set_groom_asset(None);c.set_groom_asset(asset);c.set_editor_property('binding_asset',None);c.set_visibility(True,False);c.set_hidden_in_game(False,False)
  levels.save_current_level()
# Disable all card overlays after Groom assignment; keep source hair cards hidden.
cs=temps(bp)
for n in ('SKC_HairThinHeroLockCorrected','SKC_HairThinWetOverlay','SKC_HairThinShader5','SKC_HairThinSourceCards'):
 if n in cs:cs[n].set_visibility(False,False);cs[n].set_hidden_in_game(True,False)
BlueprintTools.compile_blueprint(bp,warnings_as_errors=True);unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
for mp in MAPS:
 levels.load_level(mp);chars=[a for a in actors.get_all_level_actors() if a.get_class()==bp.generated_class()];
 if len(chars)==1:
  for c in chars[0].get_components_by_class(unreal.SkeletalMeshComponent):
   if c.get_name() in ('SKC_HairThinHeroLockCorrected','SKC_HairThinWetOverlay','SKC_HairThinShader5','SKC_HairThinSourceCards'):c.set_visibility(False,False);c.set_hidden_in_game(True,False)
  levels.save_current_level()
unreal.log('HERO_CORRECTED_GROOM_BP_ATTACHED '+GROOM)
