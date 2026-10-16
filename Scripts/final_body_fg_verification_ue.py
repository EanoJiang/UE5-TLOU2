"""Ordered final asset mutation and read-only verification session."""
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
for name in ['reimport_restored_body_only_ue.py','apply_source_fg_primary_ue.py','verify_captured_fg_stage_ue.py','verify_final_source_fidelity_compression_ue.py']:
    path=ROOT/'Scripts'/name
    exec(compile(path.read_text(),str(path),'exec'),{'__name__':'__main__'})
