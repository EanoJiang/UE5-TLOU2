"""Independently reimport FG FBX/GLB and compare source world surfaces."""
import bpy,json,hashlib
import numpy as np
from collections import Counter
from mathutils import kdtree
from pathlib import Path
ROOT=Path('D:/TLOU2_UE5_8_Codex')
manifest=json.loads((ROOT/'Exports/capture_fg_stage_manifest.json').read_text())

def triangle_key(points):
    a,b,c=points
    return min((a,b,c),(b,c,a),(c,a,b))

reports=[]
for extension in ['fbx','glb']:
    path=ROOT/'Exports'/('Catalog_CapturedFGStage.'+extension)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if extension=='fbx':bpy.ops.import_scene.fbx(filepath=str(path))
    else:bpy.ops.import_scene.gltf(filepath=str(path))
    objects=[o for o in bpy.data.objects if o.type=='MESH'];assert len(objects)==33,len(objects)
    rows=[]
    for source in manifest['rows']:
        ob=next(o for o in objects if o.name.startswith(f"Catalog_CapturedFG_{source['index']:02d}_"))
        z=np.load(source['world_posed_npz']);positions=z['posed_world_positions_blender_meters']
        indices=z['indices_raw'].view('<u2')[:source['indices']].reshape(-1,3)
        drawable=np.unique(indices);points=[tuple(float(v) for v in p) for p in positions]
        source_tree=kdtree.KDTree(len(drawable))
        for i,j in enumerate(drawable):source_tree.insert(points[j],int(j))
        source_tree.balance()
        actual=[tuple(ob.matrix_world@v.co) for v in ob.data.vertices]
        mapped=[];maximum_forward=0
        for p in actual:
            _,index,distance=source_tree.find(p);mapped.append(points[index]);maximum_forward=max(maximum_forward,distance)
        actual_tree=kdtree.KDTree(len(actual))
        for i,p in enumerate(actual):actual_tree.insert(p,i)
        actual_tree.balance()
        maximum_reverse=max(actual_tree.find(points[j])[2] for j in drawable)
        expected=Counter(triangle_key(tuple(points[j] for j in tri)) for tri in indices)
        ob.data.calc_loop_triangles()
        found=Counter(triangle_key(tuple(mapped[j] for j in tri.vertices)) for tri in ob.data.loop_triangles)
        missing=sum((expected-found).values());extra=sum((found-expected).values())
        row={'index':source['index'],'source_submesh':source['source_submesh'],'imported_mesh':ob.name,
             'source_allocated_vertices':len(positions),'source_drawable_vertices':len(drawable),'imported_vertices':len(actual),
             'source_triangles':len(indices),'imported_triangles':len(ob.data.loop_triangles),
             'bidirectional_max_error_m':max(maximum_forward,maximum_reverse),'missing_triangle_copies':missing,'extra_triangle_copies':extra,
             'pass':max(maximum_forward,maximum_reverse)<2e-5 and missing==0 and extra==0}
        rows.append(row)
    reports.append({'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mesh_count':len(rows),
                    'source_triangles':sum(r['source_triangles'] for r in rows),'imported_triangles':sum(r['imported_triangles'] for r in rows),
                    'maximum_position_error_m':max(r['bidirectional_max_error_m'] for r in rows),'pass':all(r['pass'] for r in rows),'rows':rows})
report={'pass':all(r['pass'] for r in reports),'tolerance_m':2e-5,'files':reports,
        'method':'Fresh BlenderFBX/GLBimport, worldspacepositions compared bidirectionally against each unique source subset drawablevertices. Nearestsourcecoordinate canonicalization preserves cyclicwinding and original triangle multiplicities.',
        'scope':'StaticFGworldpositions and drawable trianglecoverage only; sourceUV/normals/materialrendering and UEbuiltvertexbuffers not verified here.'}
(ROOT/'Exports/captured_fg_stage_exchange_validation.json').write_text(json.dumps(report,indent=2))
print('FG_EXCHANGE_VALIDATION',json.dumps({k:v for k,v in report.items() if k!='files'}))
for r in reports:print(r['file'],r['pass'],r['source_triangles'],r['imported_triangles'],r['maximum_position_error_m'])
if not report['pass']:raise RuntimeError('FGexchange geometry differs from source')
