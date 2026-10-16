import json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/CapturedFGStage/TexturesDecoded'
OUT.mkdir(parents=True,exist_ok=True)
rows=json.loads((ROOT/'Exports/ExactDebug/keyart_turntable_fg/texture_headers.json').read_text())
for row in rows:row['folder']='keyart_turntable_fg'
(OUT/'texture_decode_manifest.json').write_text(json.dumps(rows,indent=2))
path=ROOT/'Scripts/decode_pc_highres_textures.py'
code=path.read_text().replace('OUT = ROOT / "Exports/TexturesDecoded"','OUT = ROOT / "Exports/CapturedFGStage/TexturesDecoded"').replace('(OUT / "pc_texture_dictionary_index.json")','(ROOT / "Exports/TexturesDecoded/pc_texture_dictionary_index.json")')
exec(compile(code,str(path),'exec'),{'__name__':'__main__'})
