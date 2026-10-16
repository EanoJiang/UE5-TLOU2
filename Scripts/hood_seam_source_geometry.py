"""Read-only source-geometry identity render and seam ray audit."""
import bpy
import json
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/HoodSeam'
REPORT=ROOT/'Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rows=json.loads(REPORT.read_text())['rows']
    actor_world=Matrix(json.loads((ROOT/'Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.json').read_text())['actor_world_blender'])
    materials={}
    summary=[]
    colors={'ellie_head':(1.,.15,.1,1),'ellie_patrol_hoodie_cloth':(.05,.8,.2,1),
            'ellie_patrol_jacket':(.1,.3,1.,1),'ellie16_patrol_body':(.9,.1,.7,1)}
    for i,row in enumerate(rows):
        raw=np.load(row['source_npz'])
        ref=np.load(row['path'])
        p=ref['original_shader_weight_skinned_actor_vertices_blender']
        source_meta=json.loads(Path(row['source_capture']).read_text())
        mesh_meta=next(m for m in source_meta['meshes'] if m['name']==row['source_mesh'])
        triangles=raw['indices_raw'].view('<u2')[:mesh_meta['count']].reshape(-1,3)
        mesh=bpy.data.meshes.new('SourceMesh_%02d'%i)
        mesh.from_pydata(p.tolist(),[],triangles.tolist())
        mesh.update()
        obj=bpy.data.objects.new('Source_%02d_%s'%(i,row['source_mesh']),mesh)
        bpy.context.collection.objects.link(obj)
        obj.matrix_world=actor_world
        obj['source_row_index']=i
        obj['source_mesh']=row['source_mesh']
        obj['source_folder']=row['source_folder']
        folder=row['source_folder']
        if folder not in materials:
            mat=bpy.data.materials.new('ID_'+folder)
            mat.diffuse_color=colors.get(folder,(.25,.25,.25,1))
            mat.use_nodes=True
            nodes=mat.node_tree.nodes
            nodes.clear()
            output=nodes.new('ShaderNodeOutputMaterial')
            emit=nodes.new('ShaderNodeEmission')
            emit.inputs['Color'].default_value=mat.diffuse_color
            mat.node_tree.links.new(emit.outputs[0],output.inputs[0])
            materials[folder]=mat
        mesh.materials.append(materials[folder])
        summary.append(dict(index=i,object=obj.name,source_mesh=row['source_mesh'],source_folder=folder,
            vertices=len(p),triangles=len(triangles),color=materials[folder].diffuse_color[:]))
    camera_data=bpy.data.cameras.new('SeamCamera')
    camera=bpy.data.objects.new('SeamCamera',camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location=(0.,-1.05,1.43)
    target=Vector((.015,0.,1.37))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.type='PERSP'
    camera_data.angle=np.radians(35.)
    scene=bpy.context.scene
    scene.camera=camera
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1000
    scene.render.resolution_y=750
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new('DiagnosticWorld')
    scene.world.color=(0,0,0)
    scene.view_settings.view_transform='Standard'
    scene.render.filepath=str(OUT/'SourceGeometry_ID_Front.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'SourceGeometry_Diagnostic.blend'))
    bpy.ops.render.render(write_still=True)
    for material in materials.values():material.use_backface_culling=True
    scene.render.filepath=str(OUT/'SourceGeometry_ID_Front_BackfaceCull.png')
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=4000
    scene.render.resolution_y=3000
    scene.render.use_border=True
    scene.render.use_crop_to_border=True
    scene.render.border_min_x=.40
    scene.render.border_max_x=.56
    scene.render.border_min_y=.42
    scene.render.border_max_y=.52
    scene.render.filepath=str(OUT/'SourceGeometry_ID_SeamCrop.png')
    bpy.ops.render.render(write_still=True)
    for material in materials.values():material.use_backface_culling=False
    scene.render.filepath=str(OUT/'SourceGeometry_ID_SeamCrop_TwoSided.png')
    bpy.ops.render.render(write_still=True)
    # Precise independent nearest triangle identity for the image region.
    depsgraph=bpy.context.evaluated_depsgraph_get()
    rays=[]
    from bpy_extras.object_utils import world_to_camera_view
    for z in np.linspace(1.31,1.41,101):
        for x in np.linspace(-.015,.095,111):
            origin=actor_world@Vector((float(x),-1.,float(z)))
            direction=actor_world.to_3x3()@Vector((0,1,0))
            hit,loc,normal,face,obj,_=scene.ray_cast(depsgraph,origin,direction)
            for skip in range(20):
                if not hit or normal.dot(direction)<0:break
                origin=loc+direction*1e-7
                hit,loc,normal,face,obj,_=scene.ray_cast(depsgraph,origin,direction)
            if hit and obj.get('source_folder')=='ellie_head':
                # Keep below the main neckline; determine exact bounds after inspection.
                rays.append(dict(x=float(x),z=float(z),position=list(loc),face=face,
                    source_mesh=obj['source_mesh'],source_row_index=obj['source_row_index'],
                    camera_uv=list(world_to_camera_view(scene,camera,loc))))
    (OUT/'source_geometry_identity.json').write_text(json.dumps(dict(meshes=summary,
        camera_location=list(camera.location),camera_target=list(target),skin_ray_samples=rays),indent=2))
    perspective=[]
    tang=np.tan(camera_data.angle/2)
    rotation=camera.matrix_world.to_3x3()
    for u in np.linspace(.47,.51,161):
        for v in np.linspace(.44,.50,241):
            direction=(rotation@Vector(((u-.5)*2*tang,(v-.5)*2*tang*.75,-1))).normalized()
            origin=camera.location.copy()
            hit,loc,normal,face,obj,_=scene.ray_cast(depsgraph,origin,direction)
            for skip in range(20):
                if not hit or normal.dot(direction)<0:break
                origin=loc+direction*1e-7
                hit,loc,normal,face,obj,_=scene.ray_cast(depsgraph,origin,direction)
            if hit and obj.get('source_folder')=='ellie_head':
                perspective.append(dict(u=float(u),v=float(v),actor_position=list(actor_world.inverted()@loc),
                    face=face,vertex_ids=list(obj.data.polygons[face].vertices),
                    source_mesh=obj['source_mesh'],source_row_index=obj['source_row_index']))
    (OUT/'source_seam_perspective_rays.json').write_text(json.dumps(perspective,indent=2))
    print('HOOD_SEAM_SOURCE_GEOMETRY '+json.dumps(dict(meshes=len(summary),skin_rays=len(rays),image=scene.render.filepath)))

if __name__=='__main__':main()
