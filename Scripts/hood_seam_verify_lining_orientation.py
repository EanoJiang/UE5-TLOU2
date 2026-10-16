"""Describe the additive lining's orientation without claiming a welded shell."""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT=Path('D:/TLOU2_UE5_8_Codex')
OUT=ROOT/'Exports/HoodSeam'
z=np.load(OUT/'repair_geometry_snapshot.npz')
p=z['posed_positions_after']
source=z['triangles_before']
patch=z['triangles_after'][len(source):]
world=np.array(json.loads((ROOT/'Exports/CaptureBuffers/Ellie_Capture_SkinPalette1038.json').read_text())['actor_world_blender'])
camera=(np.linalg.inv(world)@np.array([0.,-1.05,1.43,1.]))[:3]
normals=np.cross(p[patch[:,1]]-p[patch[:,0]],p[patch[:,2]]-p[patch[:,0]])
normal_norm=np.linalg.norm(normals,axis=1)
assert (normal_norm>1e-12).all()
normals/=normal_norm[:,None]
directions=camera-p[patch].mean(1)
directions/=np.linalg.norm(directions,axis=1)[:,None]
camera_dots=(normals*directions).sum(1)
edges=defaultdict(list)
for i,tri in enumerate(patch):
    for a,b in zip(tri,np.roll(tri,-1)):
        edges[tuple(sorted((int(a),int(b))))].append((int(a),int(b),i))
shared=[rows for rows in edges.values() if len(rows)==2]
inconsistent=[rows for rows in shared if rows[0][:2]==rows[1][:2]]
a,b=1689,1690
old_face=next(t for t in source if a in t and b in t)
old_normal=np.cross(p[old_face[1]]-p[old_face[0]],p[old_face[2]]-p[old_face[0]])
old_normal/=np.linalg.norm(old_normal)
report=dict(new_faces_front_facing_at_reference=bool((camera_dots>0).all()),
    minimum_new_face_cosine_to_camera=float(camera_dots.min()),new_face_cosines_to_camera=camera_dots.tolist(),
    internal_shared_edges=len(shared),internal_inconsistent_edges=inconsistent,
    first_original_fold_triangle=old_face.tolist(),first_new_lining_vs_fold_normal_dot=float(normals[0]@old_normal),
    policy='Disconnected inner lining; original outer-fold faces untouched. Front-facing lining orientation is not a claim of welded-manifold continuity with the original fold.')
(OUT/'lining_orientation_verification.json').write_text(json.dumps(report,indent=2))
print('HOOD_SEAM_LINING_ORIENTATION '+json.dumps(report))
