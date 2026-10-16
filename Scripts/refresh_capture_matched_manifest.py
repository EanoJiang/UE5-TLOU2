import json
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
path=ROOT/'Exports/capture_matched_patrol_manifest.json'
doc=json.loads(path.read_text())
rig=json.loads((ROOT/'Exports/owned_rig_integration_report.json').read_text())
doc.update({'character_mesh_count':rig['character_meshes'],'bones':rig['bones'],'vertices':rig['vertices'],
            'human_bones':1074,'owned_hoodie_bones':78,'backpack_joint_owner':'human1074',
            'backpack_package':'ellie-backpack.pak','maximum_source_influences':12,
            'reference_metadata':rig['rest_metadata'],'source_skin_audit':'Exports/owned_rig_integration_report.json',
            'glb_skin_validation':'Exports/Ellie_Patrol_Catalog_CaptureMatched_gltf_skin_validation.json',
            'active_selection_validation':'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json',
            'plinth':'extracted original keyart-turntable geometry, portable material reconstruction',
            'eye_shader':'documented reconstructed radial iris/sclera blend; source constants unresolved',
            'supersedes':'Earlier31mesh/1074/1390prop-backpack exports are legacydebug; selected capture uses29meshes1152bones'})
doc['removed_capture_hidden_base_arms']=json.loads((ROOT/'Exports/capture_hidden_base_arms_report.json').read_text())['removed_hidden_base_arms']
path.write_text(json.dumps(doc,indent=2),encoding='utf-8')
print('FINAL_CAPTURE_MANIFEST',doc['character_mesh_count'],doc['bones'],doc['vertices'])
