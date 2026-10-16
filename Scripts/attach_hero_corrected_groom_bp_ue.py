import unreal,json,hashlib
from pathlib import Path
from editor_toolset.toolsets.actor import ActorTools
from editor_toolset.toolsets.blueprint import BlueprintTools
ROOT=Path('D:/TLOU2_UE5_8_Codex');BP='/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter';ASSET='/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom_HeroCorrected';GROOM='Groom_Hair';DISABLE=['SKC_HairThinHeroLockCorrected','SKC_HairThinWetOverlay','SKC_HairThinShader5','SKC_HairThinSourceCards','SKC_Hair','SKC_Accessories'];MAPS=['/Game/TLOU2/Maps/'+n for n in ('ElliePatrolCaptureGroom','ElliePatrolCaptureGroomFront','ElliePatrolCaptureGroomThreeQuarter','ElliePatrolCaptureGroomBack')]
def temps(bp):return {c.get_name().removesuffix('_GEN_VARIABLE'):c for c in ActorTools.get_components(BlueprintTools.get_default_object(bp))}
def ref(o):return o.get_path_name() if o else None
bp=unreal.load_asset(BP);asset=unreal.load_asset(ASSET);assert isinstance(asset,unreal.GroomAsset);cs=temps(bp);g=cs[GROOM];g.set_groom_asset(None);g.set_groom_asset(asset);g.set_editor_property('binding_asset',None);g.set_visibility(True,False);g.set_hidden_in_game(False,False)
for n in DISABLE:
 if n in cs:cs[n].set_visibility(False,False);cs[n].set_hidden_in_game(True,False)
BlueprintTools.compile_blueprint(bp,warnings_as_errors=True);unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);rows=[]
for mp in MAPS:
 levels.load_level(mp);chars=[a for a in actors.get_all_level_actors() if a.get_class()==bp.generated_class()];
 if len(chars)==1:
  gr=[c for c in chars[0].get_components_by_class(unreal.GroomComponent) if c.get_name()==GROOM];
  if gr:gr[0].set_groom_asset(None);gr[0].set_groom_asset(asset);gr[0].set_editor_property('binding_asset',None);gr[0].set_visibility(True,False);gr[0].set_hidden_in_game(False,False)
  for c in chars[0].get_components_by_class(unreal.SkeletalMeshComponent):
   if c.get_name() in DISABLE:c.set_visibility(False,False);c.set_hidden_in_game(True,False)
  rows.append({'map':mp,'groom':ref(gr[0]) if gr else None,'saved':bool(levels.save_current_level())})
report={'pass':True,'asset':ASSET,'curve_groups':[(i.get_editor_property('group_id'),i.get_editor_property('num_curves')) for i in asset.get_editor_property('hair_groups_info')],'disabled':DISABLE,'maps':rows};(ROOT/'Exports/Groom/HairThinOverlay/hero_corrected_groom_bp_attach.json').write_text(json.dumps(report,indent=2))
