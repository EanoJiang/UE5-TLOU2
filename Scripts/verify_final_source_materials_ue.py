"""Fresh-process saved material/map verification after all material writes."""
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
for name in ['verify_source_fg_primary_ue.py','verify_character_source_primary_ue.py','verify_captured_fg_stage_ue.py']:
    path=ROOT/'Scripts'/name
    exec(compile(path.read_text(),str(path),'exec'),{'__name__':'__main__'})
