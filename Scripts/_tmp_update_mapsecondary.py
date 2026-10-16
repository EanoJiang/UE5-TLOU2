import json
from pathlib import Path
p=Path(r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\Reports\bone_channel_hash_mapping_evidence.json');d=json.loads(p.read_text());d['animation']['external_joint_descriptor_scope']='secondary p-aim clip entry217; not primary lg target entry468';d['limitations'].append('The eight external joint descriptors are from the secondary p-aim clip; primary lg target external region at page9 relative 0x8e150 still needs segmentation.')
p.write_text(json.dumps(d,indent=2),encoding='utf-8')
md=Path(r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\Reports\BONE_CHANNEL_HASH_MAPPING.md');s=md.read_text();s=s.replace('the selected ANIM external joint table separately yields **8** direct bone-hash mappings','the secondary p-aim ANIM external joint table separately yields **8** direct bone-hash mappings (primary lg target remains unresolved)');s=s.replace('the selected ANIM external joint table embeds eight exact FNV bone hashes.','the secondary p-aim ANIM external joint table embeds eight exact FNV bone hashes; the primary lg target uses a different external region and remains to be segmented.')
md.write_text(s,encoding='utf-8')
