"""Persist capture-only corrective morphs in the hold animation itself."""
import unreal
import json
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
manifest=json.loads((ROOT/'Exports/captured_skin_pose_chunk_manifest.json').read_text())
anim=unreal.load_asset('/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim')
sk=anim.get_skeleton()
names=set()
mesh_rows=[]
corrections=json.loads((ROOT/'Exports/Ellie_Patrol_CapturedSkinPose_validation.json').read_text())
maximums={r['mesh']:r['maximum_bind_space_delta_m'] for r in corrections['corrective_targets']}
for chunk in manifest['chunks']:
    mesh=unreal.load_asset('/Game/TLOU2/CaptureMatched1152/CapturedMeshes/'+chunk+'/Ellie_Patrol_'+chunk+'_Pruned')
    morphs=[m.get_name() for m in mesh.get_editor_property('morph_targets') if 'CaptureAffineCorrective' in m.get_name()]
    maximum=max(maximums[m['source_mesh']] for m in manifest['chunks'][chunk]['meshes'])
    # Submicron numerical compensation can be discarded by UE morph import.
    # Require an imported target wherever the true affine correction exceeds10um.
    assert morphs or maximum<1e-5, ('No imported capture corrective morph',chunk,maximum,[m.get_name() for m in mesh.get_editor_property('morph_targets')])
    names.update(morphs)
    mesh_rows.append({'chunk':chunk,'mesh':mesh.get_path_name(),'morph_names':morphs,'source_maximum_corrective_delta_m':maximum,'required_above_10um':maximum>=1e-5})
library=unreal.AnimationLibrary
curve_type=unreal.RawCurveTrackTypes.RCT_FLOAT
for name in sorted(names):
    if not library.does_curve_exist(anim,name,curve_type): library.add_curve(anim,name,curve_type,False)
    library.add_float_curve_keys(anim,name,[0.0,float(anim.get_play_length())],[1.0,1.0])
    library.set_curve_meta_data_morph_target(sk,name,True)
    values=[library.get_float_value_at_time(anim,name,t) for t in (0.0,anim.get_play_length()/2,anim.get_play_length())]
    assert all(abs(v-1)<1e-6 for v in values),(name,values)
    assert library.get_curve_meta_data_morph_target(sk,name)
unreal.EditorAssetLibrary.save_loaded_asset(sk)
unreal.EditorAssetLibrary.save_loaded_asset(anim)
out={'pass':True,'animation':anim.get_path_name(),'skeleton':sk.get_path_name(),'curve_names':sorted(names),'meshes':mesh_rows,
     'policy':'Constant1 morph curves serialized in the capture hold animation. Original one-frame and0FW source animations have no capture-only corrective. Runtime actor tags also restore overrides.'}
(ROOT/'Exports/captured_corrective_curve_validation.json').write_text(json.dumps(out,indent=2))
unreal.log('CAPTURE_CORRECTIVES_PERSISTED '+str(sorted(names)))
