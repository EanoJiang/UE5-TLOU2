"""Numerically compare the saved/reimported capture pose to raw-shader LBS."""
import bpy
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/Drawstring'

def inspect(reference):
    arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    obj=next(o for o in bpy.data.objects if o.type=='MESH')
    assert len(arm.data.bones)==22
    assert len(obj.data.vertices)==441 and len(obj.data.polygons)==736
    key=obj.data.shape_keys.key_blocks.get('CaptureAffineCorrective')
    assert key is not None,'capture affine morph absent'
    scene=bpy.context.scene
    samples=[]
    for frame in (1,2):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        assert abs(key.value-1.)<1e-6,('corrective curve',frame,key.value)
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh()
        try:positions=np.array([(obj.matrix_world@v.co)[:] for v in mesh.vertices])
        finally:evaluated.to_mesh_clear()
        # Exporter/importer vertex order is checked separately by source gate.
        error=float(np.linalg.norm(positions-reference,axis=1).max())
        assert error<1e-5,('capture shader/FBX vertex error',frame,error)
        samples.append(dict(frame=frame,max_shader_vertex_error_m=error))
    return dict(vertices=441,triangles=736,bones=22,morph_name=key.name,morph_value=key.value,samples=samples)

def main():
    reference=OUT/'captured_reference.npz'
    assert reference.exists(),'Captured reference not generated yet'
    expected=np.load(reference)['captured_positions_actor_blender_m']
    independent=np.load(OUT/'drawstring_independent_skinning.npz')['original_shader_weight_skinned_actor_vertices_blender']
    reference_error=float(np.linalg.norm(expected-independent,axis=1).max())
    assert reference_error<1e-7,('independent raw-shader reference error',reference_error)
    sys.path.insert(0,str(ROOT/'Scripts'))
    from drawstring_verify_blender import inspect as inspect_source
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blender/Ellie_Patrol_Drawstrings_Captured.blend'))
    native=inspect(expected)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT/'SK_Ellie_Patrol_Drawstrings.fbx'),use_anim=True)
    reimported=inspect(expected)
    source=inspect_source()
    result=dict(native=native,fbx_roundtrip=reimported,fbx_source_preservation=source,
        independent_shader_reference_max_error_m=reference_error,pass_=True)
    result['pass']=result.pop('pass_')
    (OUT/'captured_fbx_verification.json').write_text(json.dumps(result,indent=2))
    print('DRAWSTRING_CAPTURED_FBX_VERIFY '+json.dumps(result))

if __name__=='__main__':main()
