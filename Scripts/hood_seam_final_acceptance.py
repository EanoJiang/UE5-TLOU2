"""Aggregate fresh export, saved-asset, CPU-skin and rendered endpoint evidence."""
import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/HoodSeam'
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
checks={}
report={'pass':False,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks}
try:
    export,imp,saved,native,independent,endpoint=(read(n) for n in ('repair_export.json','ue_import.json','ue_saved_verification.json','runtime_vertex_verification.json','Independent_Final_Review.json','Independent_Runtime_Endpoint_Final.json'))
    original=read('ue_import_initial.json')
    asset=ROOT/'Content/TLOU2/CaptureMatched1152/CapturedMeshes/body_clothing/Ellie_Patrol_body_clothing_Pruned.uasset'
    checks['final_source_export_pass']=export['pass']
    checks['final_source_hash_matches_import']=sha(export['fbx'])==export['fbx_sha256']==imp['fbx_sha256']==sha(imp['fbx'])
    checks['final_saved_mesh_hash_matches_import']=sha(asset)==imp['after_sha256']
    checks['saved_reload_verification_pass']=saved['pass'] and all(saved['checks'].values())
    checks['native_runtime_verification_pass']=native['pass'] and all(native['checks'].values())
    checks['native_full_influence_capacity']=native['maximum_bone_influences']==12
    checks['native_corrective_active']=native['morph_overrides'].get('CaptureAffineCorrective')==1.0
    checks['native_uses_final_source_manifest']=native['files']['export_manifest_sha256']==sha(OUT/'repair_export.json')
    checks['native_reference_fresh']=native['files']['reference_sha256']==sha(OUT/'repair_body_reference.npz')
    checks['independent_final_source_hash']=independent['fbx_sha256']==export['fbx_sha256']
    checks['independent_source_review_pass']=independent['ready_for_ue_validation']
    checks['independent_endpoint_render_pass']=endpoint['pass']
    checks['new_geometry_count']=imp['triangles_after']==export['expected_body_triangles']==46249+export['patch']['new_triangles']
    checks['all_external_assets_preserved_during_final_mesh_import']=all(sha(p)==h for p,h in imp['external_asset_hashes_preserved'].items())
    concurrent=[]
    for path,before in original['external_asset_hashes_preserved'].items():
        current=sha(path)
        if current!=before:
            concurrent.append({'path':path,'initial_sha256':before,'current_sha256':current,
                               'final_import_before_sha256':imp['external_asset_hashes_preserved'].get(path)})
    bp_path=str(ROOT/'Content/TLOU2/Blueprints/BP_ElliePatrolCharacter.uasset')
    # An explicitly user-requested Groom task updated this shared BP at00:43
    # while seam diagnostics were running. Preserve that newer authoring work.
    evidence=ROOT/'Saved/Logs/TLOU2Codex-backup-2026.10.16-16.43.15.log'
    evidence_text=evidence.read_text(encoding='utf-8',errors='replace')
    expected_bp_update='[2026.10.16-16.43.14:' in evidence_text and 'Saving Package: /Game/TLOU2/Blueprints/BP_ElliePatrolCharacter' in evidence_text
    checks['initial_external_assets_preserved_except_verified_concurrent_groom_update']=all(row['path']==bp_path and row['current_sha256']==row['final_import_before_sha256'] for row in concurrent) and (not concurrent or expected_bp_update)
    report['concurrent_external_changes']={'changes':concurrent,'evidence_log':str(evidence),'evidence_log_sha256':sha(evidence),
        'source_task':'复刻截帧角色头发 Groom','thread_id':'01a1441b-c479-71c0-9f9c-d7d9bea0ba2b',
        'reason':'Separate user-requested HeroFringe Groom/physics update during seam work; final seam import preserved that newer BP and final spawned/placed/runtime checks retain drawstrings and cloth animation.'}
    checks['canonical_blend_unchanged']=sha(export['source_blend'])==export['source_blend_sha256']
    checks['original_backup_valid']=sha(original['backup'])==original['before_sha256'] and original['triangles_before']==46249
    views={}
    for view in ('Front','Left','Right'):
        suffix='' if view=='Front' else '_'+view
        image=OUT/('Fixed'+suffix+'.png')
        probe=read('runtime_Fixed'+suffix+'.json')
        body=next(r for r in probe['rows'] if r['component']=='SKC_BodyClothing')
        strings=next(r for r in probe['rows'] if r['component']=='SKC_Drawstrings')
        checks[view+'_fresh_actual_game_image']=image.is_file() and image.stat().st_mtime>asset.stat().st_mtime
        checks[view+'_independent_endpoint_image_hash']=endpoint['views'][view]['sha256']==sha(image)
        checks[view+'_uses_original_body_asset']=body['mesh']==imp['asset']
        checks[view+'_cloth_animation_preserved']=body['anim_class']==imp['body_anim_class_before']
        checks[view+'_drawstrings_visible']=strings['visible_before'] and '/Drawstring/SK_Ellie_Patrol_Drawstrings.' in strings['mesh']
        checks[view+'_corrective_active']=body['animation_curves'].get('CaptureAffineCorrective')==1.0
        views[view]={'image':str(image),'image_sha256':sha(image),'probe':str(OUT/('runtime_Fixed'+suffix+'.json'))}
    report.update(asset=str(asset),source_fbx=export['fbx'],source_fbx_sha256=export['fbx_sha256'],
                  triangles_before=46249,triangles_after=imp['triangles_after'],new_vertices=export['patch']['new_vertices'],
                  new_triangles=export['patch']['new_triangles'],native_max_position_error_mm=native['max_bidirectional_error_mm'],
                  original_backup=original['backup'],views=views,
                  scope='Localized new lining fitted between original capture garment boundaries. Existing source geometry, rig, corrective morph, materials, drawstrings, animation blueprints and maps preserved; isolated diagnostic map added.')
    assert all(checks.values()), [k for k,v in checks.items() if not v]
    report['pass']=True
except Exception:
    report['error']=traceback.format_exc()
finally:
    (OUT/'final_acceptance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if not report['pass']:raise SystemExit(1)
