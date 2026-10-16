import json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex');out=ROOT/'Exports/PlinthTexturesDecoded';out.mkdir(exist_ok=True);rows=[];seen=set()
for f in ['keyart_turntable_wet_large','keyart_turntable_concrete_large']:
 for r in json.load(open(ROOT/'Exports/ExactDebug'/f/'texture_headers.json')):
  if r['hash'] in seen:continue
  seen.add(r['hash']);r['folder']=f;rows.append(r)
json.dump(rows,open(out/'texture_decode_manifest.json','w'),indent=2)
code=(ROOT/'Scripts/decode_pc_highres_textures.py').read_text().replace('OUT = ROOT / "Exports/TexturesDecoded"','OUT = ROOT / "Exports/PlinthTexturesDecoded"').replace('(OUT / "pc_texture_dictionary_index.json")','(ROOT / "Exports/TexturesDecoded/pc_texture_dictionary_index.json")')
exec(compile(code,str(ROOT/'Scripts/decode_pc_highres_textures.py'),'exec'))
