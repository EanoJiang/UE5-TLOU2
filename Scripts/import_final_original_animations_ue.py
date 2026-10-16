import unreal
import json
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
skpath='/Game/TLOU2/CaptureMatched1152/Skeleton/Ellie_CaptureMatched1152_SkeletonCarrier_Skeleton'
sk=unreal.load_asset(skpath)
assert sk and len(sk.get_reference_pose().get_bone_names())==1153
rows=[]
for name in ('Ellie_Patrol_Original_0FW_AnimationCarrier','Ellie16_Patrol_OriginalViewerPose_UEHoldCarrier'):
    task=unreal.AssetImportTask()
    task.filename=str(ROOT/'Exports'/(name+'.fbx'))
    task.destination_path='/Game/TLOU2/CaptureMatched1152/Animations'
    task.automated=True
    task.replace_existing=True
    task.save=True
    options=unreal.FbxImportUI()
    for key,value in {'import_mesh':True,'import_as_skeletal':True,'import_animations':True,
                      'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':sk}.items():
        options.set_editor_property(key,value)
    task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    animations=[unreal.load_asset(p) for p in task.imported_object_paths]
    animations=[a for a in animations if isinstance(a,unreal.AnimSequence)]
    assert len(animations)==1, list(task.imported_object_paths)
    anim=animations[0]
    anim.set_editor_property('enable_root_motion',False)
    unreal.EditorAssetLibrary.save_loaded_asset(anim)
    assert anim.get_skeleton()==sk
    rows.append({'asset':anim.get_path_name(),'seconds':float(anim.get_play_length()),'source':task.filename,'same_skeleton':True})
(ROOT/'Exports/import_final_original_animations_result.json').write_text(json.dumps({'skeleton':skpath,'animations':rows,'pass':True},indent=2))
unreal.log('FINAL_ORIGINAL_ANIMATIONS_IMPORT '+str(rows))
