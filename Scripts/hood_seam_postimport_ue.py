"""Fresh saved-asset verification and independent native audit map creation."""
from pathlib import Path
root=Path('D:/TLOU2_UE5_8_Codex/Scripts')
for name in ('hood_seam_verify_saved_ue.py','hood_seam_diagnostic_map_ue.py'):
    script=root/name
    exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
