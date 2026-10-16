"""FG mutation and checks after body reimport has already completed."""
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
for name in ['apply_source_fg_primary_ue.py','verify_captured_fg_stage_ue.py','verify_final_source_fidelity_compression_ue.py']:
    path=ROOT/'Scripts'/name
    exec(compile(path.read_text(),str(path),'exec'),{'__name__':'__main__'})
