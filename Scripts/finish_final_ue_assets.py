from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
for script in ('import_final_original_animations_ue.py','persist_capture_corrective_curves_ue.py',
               'export_final_original_ue_poses.py','verify_capture_matched_catalog_map_ue.py','verify_catalog_controls_ue.py'):
    path=ROOT/'Scripts'/script
    exec(compile(path.read_text(),str(path),'exec'),{'__name__':'__main__'})
