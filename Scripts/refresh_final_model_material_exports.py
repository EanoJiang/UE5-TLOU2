"""Pack final portable materials and refresh interchange without changing rig/actions."""
import bpy
import sys
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
source=Path(sys.argv[sys.argv.index('--')+1])
path=ROOT/'Scripts/apply_final_material_portability_blender.py'
exec(compile(path.read_text(),str(path),'exec'),{'__name__':'__main__'})
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
has_animation=bool(arm.animation_data and arm.animation_data.action)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)]
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for obj in meshes: obj.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=str(ROOT/'Exports'/(source.stem+'.fbx')),use_selection=True,
    object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=has_animation,bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_step=1.0,bake_anim_simplify_factor=0,
    apply_unit_scale=True,axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',use_custom_props=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Exports'/(source.stem+'.glb')),export_format='GLB',use_selection=True,
    export_animations=has_animation,export_all_influences=True)
print('FINAL_MODEL_MATERIAL_EXPORT',source,len(meshes),len(arm.data.bones))
