"""Reconstruct a static Groom from Ellie's original captured hair cards.

Run with Blender --background --python this_file. No original file is modified.
The source is evaluated at frame 1 (including CaptureAffineCorrective). Each
strand follows an opacity-weighted UV trajectory on one source card island.
This reconstructs card flow, silhouette and clumping, not unavailable authoring
curves. The companion manifest states the resulting limits explicitly.
"""
from pathlib import Path
import hashlib
import json
import math
import time
import numpy as np

ROOT = Path('D:/TLOU2_UE5_8_Codex')
SOURCE = ROOT / 'Blender/Ellie_Patrol_CapturedSkinPose.blend'
OUT_BLEND = ROOT / 'Blender/Ellie_Patrol_CaptureGroom.blend'
OUT = ROOT / 'Exports/Groom'
SEED = 20261016
POINTS = 24
TARGETS = {'thick': 36000, 'thin': 16000, 'flyaway': 1400, 'wet': 1800}
GROUP_IDS = {'thick': 0, 'thin': 1, 'flyaway': 2, 'wet': 3}


def blender_m_to_ue_cm(points):
    return np.asarray(points) * np.array([100., -100., 100.])


def uv_to_xyz(points, triangles_uv, triangles_xyz, return_triangles=False):
    """Barycentric UV lookup; absent samples stay NaN, never bridge UV holes."""
    p = np.asarray(points, dtype=np.float64)
    result = np.full((len(p), 3), np.nan, dtype=np.float64)
    which = np.full(len(p), -1, dtype=np.int32)
    for index, (uv, xyz) in enumerate(zip(triangles_uv, triangles_xyz)):
        edge1, edge2 = uv[1] - uv[0], uv[2] - uv[0]
        det = edge1[0] * edge2[1] - edge1[1] * edge2[0]
        if abs(det) < 1e-12:
            continue
        candidate = np.flatnonzero((which < 0) & np.all(p >= uv.min(0) - 1e-7, axis=1) & np.all(p <= uv.max(0) + 1e-7, axis=1))
        if not len(candidate):
            continue
        delta = p[candidate] - uv[0]
        b = (delta[:, 0] * edge2[1] - delta[:, 1] * edge2[0]) / det
        c = (edge1[0] * delta[:, 1] - edge1[1] * delta[:, 0]) / det
        inside = (b >= -1e-6) & (c >= -1e-6) & (b + c <= 1 + 1e-6)
        selected = candidate[inside]
        result[selected] = xyz[0] + b[inside, None] * (xyz[1] - xyz[0]) + c[inside, None] * (xyz[2] - xyz[0])
        which[selected] = index
    if return_triangles:
        return result, which >= 0, which
    return result, which >= 0


def weighted_u_paths(u, alpha, quantiles):
    """Transport fixed opacity-mass quantiles along atlas V, following its flow."""
    out = np.full((len(alpha), len(quantiles)), np.nan)
    for row, values in enumerate(alpha):
        total = values.sum()
        if total > 1e-8:
            # Midpoint CDF avoids a systematic half-texel lateral offset.
            cdf = (np.cumsum(values) - .5 * values) / total
            keep = values > 1e-8
            out[row] = np.interp(quantiles, cdf[keep], u[keep])
    return out


def longest_true_run(valid):
    padded = np.r_[False, valid, False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    stops = np.flatnonzero(np.diff(padded) == -1)
    if not len(starts):
        return 0, 0
    i = int(np.argmax(stops - starts))
    return int(starts[i]), int(stops[i])


def orient_root(curve, scalp_distance):
    reverse = scalp_distance(curve[-1]) + 1e-8 < scalp_distance(curve[0])
    return (curve[::-1].copy() if reverse else curve.copy()), bool(reverse)


def sample_image(image, uv):
    h, w = image.shape
    x = np.clip(uv[..., 0], 0, 1) * (w - 1)
    y = np.clip(uv[..., 1], 0, 1) * (h - 1)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    dx, dy = x - x0, y - y0
    return ((1 - dy) * ((1 - dx) * image[y0, x0] + dx * image[y0, x1]) +
            dy * ((1 - dx) * image[y1, x0] + dx * image[y1, x1]))


def resample_curve(points, n=POINTS):
    lengths = np.r_[0., np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    keep = np.r_[True, np.diff(lengths) > 1e-9]
    lengths, points = lengths[keep], points[keep]
    if len(points) < 2 or lengths[-1] < .002:
        return None
    at = np.linspace(0, lengths[-1], n)
    return np.column_stack([np.interp(at, lengths, points[:, axis]) for axis in range(3)])


def evaluated_islands(obj, depsgraph, opacity):
    """Split at topology discontinuities and UV seams before sampling cards."""
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        matrix = np.asarray(evaluated.matrix_world, dtype=float)
        xyz = np.empty((len(mesh.vertices), 3), dtype=np.float64)
        mesh.vertices.foreach_get('co', xyz.ravel())
        xyz = xyz @ matrix[:3, :3].T + matrix[:3, 3]
        uv = np.array([tuple(x.uv) for x in mesh.uv_layers[0].data])
        n_poly = len(mesh.polygons)
        parent = np.arange(n_poly)
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        def union(a, b):
            a, b = find(a), find(b)
            if a != b:
                parent[b] = a
        edges = {}
        for poly in mesh.polygons:
            indices = list(poly.loop_indices)
            for a, b in zip(indices, indices[1:] + indices[:1]):
                va, vb = mesh.loops[a].vertex_index, mesh.loops[b].vertex_index
                ua, ub = tuple(np.round(uv[a], 6)), tuple(np.round(uv[b], 6))
                key = (va, vb, ua, ub) if va < vb else (vb, va, ub, ua)
                if key in edges:
                    union(poly.index, edges[key])
                else:
                    edges[key] = poly.index
        triangle_sets = {}
        for tri in mesh.loop_triangles:
            key = find(tri.polygon_index)
            triangle_sets.setdefault(key, []).append(tri)
        islands = []
        for island_index, tris in enumerate(triangle_sets.values()):
            tuv = np.array([[uv[i] for i in t.loops] for t in tris])
            txyz = np.array([[xyz[i] for i in t.vertices] for t in tris])
            lo, hi = tuv.min((0, 1)), tuv.max((0, 1))
            if min(hi - lo) < 1e-5:
                continue
            cross = np.cross(txyz[:, 1] - txyz[:, 0], txyz[:, 2] - txyz[:, 0])
            areas = np.linalg.norm(cross, axis=1) * .5
            area = float(areas.sum())
            if area < 1e-9:
                continue
            normals = cross / np.maximum(np.linalg.norm(cross, axis=1)[:, None], 1e-12)
            # 192 V stations retain curved/fan atlas trajectories before their
            # final 24-point equal-arclength resampling.
            us = np.linspace(lo[0] + 1e-6, hi[0] - 1e-6, max(96, min(512, int((hi[0]-lo[0])*opacity.shape[1]*1.5))))
            vs = np.linspace(lo[1] + 1e-6, hi[1] - 1e-6, 192)
            raster = np.stack(np.meshgrid(us, vs), -1)
            _, valid = uv_to_xyz(raster.reshape(-1, 2), tuv, txyz)
            alpha = sample_image(opacity, raster) * valid.reshape(raster.shape[:2])
            alpha[alpha < .035] = 0
            coverage = float(np.mean(alpha))
            if coverage < .00005:
                continue
            islands.append({'object': obj.name, 'index': island_index, 'uv': tuv, 'xyz': txyz,
                            'normals': normals, 'u': us, 'v': vs, 'alpha': alpha,
                            'area_m2': area, 'coverage': coverage,
                            'weight': area * coverage, 'uv_min': lo.tolist(), 'uv_max': hi.tolist()})
        return islands
    finally:
        evaluated.to_mesh_clear()


def image_array(image):
    data = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(data)
    return data.reshape(image.size[1], image.size[0], 4)[..., :3].mean(2)


def object_group(obj):
    name = obj.name
    if 'wet_extra' in name:
        return 'wet'
    if 'hair_flying' in name:
        return 'flyaway'
    if 'hair_thick' in name:
        return 'thick'
    if 'hair_thin' in name:
        return 'thin'
    return None


def make_strands(island, count, rng, scalp_distance, group):
    # Stratified quantiles avoid identical duplicated centerlines.
    quantiles = (np.arange(count) + rng.uniform(.05, .95, count)) / count
    u_paths = weighted_u_paths(island['u'], island['alpha'], quantiles)
    v_paths = np.broadcast_to(island['v'][:, None], u_paths.shape)
    all_uv = np.stack((u_paths, v_paths), -1)
    finite = np.isfinite(all_uv).all(2)
    safe_uv = np.nan_to_num(all_uv).reshape(-1, 2)
    xyz, inside, tri_ids = uv_to_xyz(safe_uv, island['uv'], island['xyz'], True)
    xyz = xyz.reshape(*u_paths.shape, 3)
    inside = inside.reshape(u_paths.shape) & finite
    tri_ids = tri_ids.reshape(u_paths.shape)
    alpha = sample_image(island['opacity'], np.nan_to_num(all_uv))
    valid = inside & (alpha >= .025)
    curves, records = [], []
    for column in range(count):
        start, stop = longest_true_run(valid[:, column])
        if stop - start < 10:
            continue
        raw = xyz[start:stop, column]
        # Reject a quantile trajectory switching between disconnected thin
        # alpha traces: a single large spatial jump is never a hair segment.
        steps = np.linalg.norm(np.diff(raw, axis=0), axis=1)
        if len(steps) and steps.max() > max(.009, np.median(steps) * 18):
            continue
        curve = resample_curve(raw)
        if curve is None:
            continue
        curve, flipped = orient_root(curve, scalp_distance)
        normals = island['normals'][np.maximum(tri_ids[start:stop, column], 0)]
        normal = normals.mean(0)
        normal /= max(np.linalg.norm(normal), 1e-12)
        # Give each source-card layer a sub-millimeter thickness. These
        # displacements are deterministic and vanish at roots; no procedural
        # haircut or global head primitive is used to invent strand flow.
        t = np.linspace(0, 1, POINTS)
        offset = rng.uniform(-.00045, .00045) * np.sin(np.pi * t) ** 1.2
        curve += offset[:, None] * normal
        length = float(np.linalg.norm(np.diff(curve, axis=0), axis=1).sum())
        root_d, tip_d = scalp_distance(curve[0]), scalp_distance(curve[-1])
        root_uv = all_uv[(stop - 1 if flipped else start), column].copy()
        curves.append(curve.astype(np.float32))
        records.append((island['object'], island['index'], root_uv, flipped, length, root_d, tip_d))
    return curves, records


def create_curve_object(name, curves, widths_mm, material, collection, group_id, export=False):
    import bpy
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_resolution = 0
    # Alembic exports curves, not a beveled mesh. Blender preview uses the
    # physical radius; per-point radius adds a short root and long tip taper.
    data.bevel_depth = .000035 if not export else .0035
    data.resolution_u = 1
    for curve, width in zip(curves, widths_mm):
        spline = data.splines.new('POLY')
        spline.points.add(len(curve) - 1)
        co = np.column_stack((curve, np.ones(len(curve), dtype=np.float32)))
        spline.points.foreach_set('co', co.ravel())
        # Alembic writer uses 2 * point.radius directly and ignores bevel_depth.
        radius = np.ones(len(curve), dtype=np.float32) * (width * .05 if export else width / .07)
        radius[0] *= .7
        radius[-8:] *= np.linspace(1, .08, 8)
        spline.points.foreach_set('radius', radius)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    if material is not None:
        data.materials.append(material)
    obj['groom_group_id'] = group_id
    obj['groom_guide'] = 0
    # The curve writer reads data-ID custom properties, not Xform object props.
    data['groom_group_id'] = group_id
    data['groom_group_id_AbcGeomScope'] = 'con'
    data['groom_guide'] = 0
    data['groom_guide_AbcGeomScope'] = 'con'
    obj['reconstruction'] = 'capture-evaluated card UV opacity-mass trajectories'
    obj['width_mm_min'] = float(np.min(widths_mm))
    obj['width_mm_max'] = float(np.max(widths_mm))
    return obj


def hair_material(group):
    import bpy
    material = bpy.data.materials.new('M_CaptureGroom_' + group)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfHairPrincipled')
    shader.parametrization = 'MELANIN'
    shader.inputs['Melanin'].default_value = .78
    shader.inputs['Melanin Redness'].default_value = .33
    shader.inputs['Roughness'].default_value = .32 if group == 'wet' else .46
    shader.inputs['Radial Roughness'].default_value = .5
    material.node_tree.links.new(shader.outputs[0], output.inputs['Surface'])
    material.diffuse_color = (.075, .035, .018, 1)
    return material


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_alembic(abc_path, curves_cm, group_ids):
    """Read both legacy and Blender 5.2 Curves import results numerically."""
    import bpy
    verify_scene = bpy.data.scenes.new('Groom_Alembic_Roundtrip_Verification')
    bpy.context.window.scene = verify_scene
    bpy.ops.wm.alembic_import(filepath=str(abc_path), set_frame_range=False, validate_meshes=True, always_add_cache_reader=True)
    verify_scene.frame_set(1)
    roundtrip = []
    for group in GROUP_IDS:
        candidates = [o for o in verify_scene.objects if o.type in ('CURVE', 'CURVES') and o.name.startswith('Groom_Ellie_' + group)]
        # Blender 5.2's reader represents the Xform and child shape with
        # duplicate Curves datablocks. Validate the leaf shape exactly once.
        leaves = [o for o in candidates if not any(c.type in ('CURVE', 'CURVES') for c in o.children)]
        if len(leaves) != 1:
            raise RuntimeError(f'Expected one imported leaf shape for {group}, found {len(leaves)}')
        obj = leaves[0]
        expected = curves_cm[group_ids == GROUP_IDS[group]]
        if obj.type == 'CURVES':
            flat = np.empty((len(obj.data.points), 3), np.float32)
            obj.data.attributes['position'].data.foreach_get('vector', flat.ravel())
            counts = np.array([c.points_length for c in obj.data.curves])
            if not np.all(counts == POINTS):
                raise RuntimeError('Alembic points-per-curve changed for ' + group)
            got = flat.reshape(-1, POINTS, 3)
            widths = np.empty(len(obj.data.points), np.float32)
            obj.data.attributes['radius'].data.foreach_get('value', widths)
        else:
            got = np.array([[tuple(p.co[:3]) for p in s.points] for s in obj.data.splines], np.float32)
            widths = np.array([p.radius for s in obj.data.splines for p in s.points], np.float32)
        recovered_ue = got[..., [0, 2, 1]].copy()
        recovered_ue[..., 2] *= -1
        if recovered_ue.shape != expected.shape:
            raise RuntimeError(f'Alembic curve count mismatch: {group}: {recovered_ue.shape} != {expected.shape}')
        error = float(np.max(np.abs(recovered_ue - expected)))
        if error > .0002:
            raise RuntimeError(f'Alembic roundtrip coordinate error: {group}: {error} cm')
        roundtrip.append({'group': group, 'curves': len(got), 'points_per_curve': len(got[0]),
                          'max_abs_coordinate_error_cm': error, 'blender_import_curve_objects': len(candidates),
                          'validated_leaf_shapes': len(leaves), 'imported_radius_cm_min_max': [float(widths.min()), float(widths.max())],
                          'raw_abc_ue_cm_bounds': [recovered_ue.min((0, 1)).tolist(), recovered_ue.max((0, 1)).tolist()]})
    return roundtrip


def attach_native_canonical(manifest):
    """Attach a newer independently verified native archive when available."""
    report_path = OUT / 'native_grouped_abc_verification.json'
    grouped_path = OUT / 'Ellie_Patrol_CaptureGroom_Grouped.abc'
    raw_path = OUT / 'Ellie_Patrol_CaptureGroom.abc'
    if not report_path.exists() or not grouped_path.exists():
        return
    if min(report_path.stat().st_mtime, grouped_path.stat().st_mtime) < raw_path.stat().st_mtime:
        return  # Do not reuse a stale native audit after a new source build.
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not report.get('pass') or not report.get('unique_geometry_bitwise_unchanged'):
        raise RuntimeError('Native canonical archive report is not a geometry-preserving pass')
    if report['curve_count'] != manifest['curve_count'] or report['point_count'] != manifest['point_count']:
        raise RuntimeError('Native canonical archive counts differ from source NPZ')
    manifest['outputs']['abc_raw'] = manifest['outputs']['abc']
    manifest['outputs']['abc'] = str(grouped_path)
    manifest['outputs']['native_verification'] = str(report_path)
    manifest['sha256']['abc_raw'] = manifest['sha256']['abc']
    manifest['sha256']['abc'] = sha256(grouped_path)
    manifest['canonical_archive'] = {
        'path': str(grouped_path), 'curve_shapes': len(report['groups']),
        'curve_count': report['curve_count'], 'point_count': report['point_count'],
        'unique_geometry_bitwise_unchanged': True,
        'raw_duplicate_shapes_removed': report['duplicate_source_shapes_removed'],
        'standard_attributes': 'groom_group_id constant int32, groom_width vertex float; standard Alembic width scope normalized to vertex without modifying width values',
        'verification_report': str(report_path), 'tool_source': str(ROOT / 'Scripts/groom_abc_attributes.cpp'),
    }


def finalize_existing():
    """Finish verification/manifest after export without regenerating strands."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    started = time.time()
    archive = np.load(OUT / 'Ellie_Patrol_CaptureGroom_curves.npz')
    curves_m, curves_cm = archive['positions_blender_m'], archive['positions_cm']
    group_ids, widths_mm = archive['group_ids'], archive['widths_mm']
    source_indices, island_indices = archive['source_object_index'], archive['source_island_index']
    object_names = archive['source_object_names'].tolist()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    scalp = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('SM_patrol_hair_base_'))
    evaluated = scalp.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    bvh = BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices], [tuple(p.vertices) for p in mesh.polygons])
    evaluated.to_mesh_clear()
    input_report = []
    for index, name in enumerate(object_names):
        obj = bpy.data.objects[name]
        material = obj.data.materials[0]
        image = next(n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and 'Opacity' in n.name)
        unique_islands, counts = np.unique(island_indices[source_indices == index], return_counts=True)
        input_report.append({'object': name, 'group': object_group(obj), 'material': material.name,
                             'opacity_image': bpy.path.abspath(image.filepath), 'opacity_resolution': list(image.size),
                             'vertices': len(obj.data.vertices), 'triangles': len(obj.data.polygons),
                             'accepted_source_islands': len(unique_islands), 'accepted_curves': int(counts.sum()),
                             'capture_affine_corrective': float(obj.data.shape_keys.key_blocks['CaptureAffineCorrective'].value) if obj.data.shape_keys and 'CaptureAffineCorrective' in obj.data.shape_keys.key_blocks else None,
                             'source_island_curve_counts': dict(zip(unique_islands.tolist(), counts.tolist()))})
    groups = []
    for group, group_id in GROUP_IDS.items():
        subset = curves_cm[group_ids == group_id]
        subset_m = curves_m[group_ids == group_id]
        lengths = np.linalg.norm(np.diff(subset, axis=1), axis=2).sum(1)
        roots = np.array([bvh.find_nearest(Vector(p))[3] * 100 for p in subset_m[:, 0]])
        tips = np.array([bvh.find_nearest(Vector(p))[3] * 100 for p in subset_m[:, -1]])
        groups.append({'name': group, 'group_id': group_id, 'curve_count': len(subset), 'point_count': len(subset) * POINTS,
                       'bounds_ue_cm': [subset.min((0, 1)).tolist(), subset.max((0, 1)).tolist()],
                       'length_cm_min_median_max': np.percentile(lengths, [0, 50, 100]).tolist(),
                       'root_scalp_distance_cm_median_p95': np.percentile(roots, [50, 95]).tolist(),
                       'tip_scalp_distance_cm_median_p95': np.percentile(tips, [50, 95]).tolist(),
                       'root_endpoint_nearer_than_tip_count': int((roots <= tips + 1e-4).sum())})
    abc_path = OUT / 'Ellie_Patrol_CaptureGroom.abc'
    roundtrip = verify_alembic(abc_path, curves_cm, group_ids)
    manifest = {
        'source_blend': str(SOURCE), 'source_blend_sha256': sha256(SOURCE), 'source_frame': 1,
        'source_capture': 'D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture',
        'created_by': str(Path(__file__)), 'seed': SEED,
        'method': 'UV-connected components of evaluated original hair cards; 192 V stations per island, opacity-mass U quantile transport, barycentric UV-to-original-triangle lookup, longest opaque run, discontinuity rejection, scalp-distance root orientation, equal-arclength 24-point resampling. A deterministic normal spread <=0.45mm adds thickness while vanishing at each root.',
        'root_method': 'Endpoint nearest original evaluated scalp-base triangles; no generic head primitive. Root location remains the original card endpoint.',
        'editable_blend_basis': 'original Blender meters and captured frame1 pose; source actual hair cards hidden, source scalp-base cap retained',
        'abc_axis': 'RAW Alembic coordinates are Unreal actor-local centimeters U=(100source.x,-100source.y,100source.z). Export-only precoords B=(U.x,-U.z,U.y) compensate Blender exporter raw=(B.x,B.z,-B.y). UE importer conversion rotation=(0,0,0), scale=(1,1,1).',
        'alembic_curve_type': 'legacy Blender CURVE / POLY authoring; 24 points, one static sample. Native SDK reader independently found two identical OCurves shapes per group in raw Blender5.2 export; canonical native Grouped archive deduplicates them.',
        'curve_count': len(curves_cm), 'points_per_curve': POINTS, 'point_count': len(curves_cm) * POINTS,
        'bounds_ue_cm': [curves_cm.min((0, 1)).tolist(), curves_cm.max((0, 1)).tolist()],
        'group_ids': GROUP_IDS, 'groups': groups, 'inputs': input_report,
        'width_mm_min_max': [float(widths_mm.min()), float(widths_mm.max())],
        'width_policy': '0.05..0.08mm shaft diameter; sparse flyaways use 0.85 times that diameter; last eight vertices taper to 8%; root tapers to 70%. Export point.radius=width_mm*0.05 cm.',
        'npz_arrays': {k: {'shape': list(archive[k].shape), 'dtype': str(archive[k].dtype)} for k in archive.files},
        'roundtrip_verification': roundtrip,
        'raw_archive_warning': {'raw_curve_shapes': 8, 'raw_curve_count': len(curves_cm) * 2,
                                'unique_reconstructed_curve_count': len(curves_cm),
                                'evidence': 'Independent native Alembic SDK reader (groom_api_audit) found duplicate arrays for each group. Leaf-only Blender roundtrip checks validate geometry but do not validate raw archive uniqueness.',
                                'policy': 'Use native deduplicated Grouped.abc as canonical UE source; preserve raw archive as generator intermediate.'},
        'outputs': {'abc': str(abc_path), 'npz': str(OUT / 'Ellie_Patrol_CaptureGroom_curves.npz'), 'blend': str(OUT_BLEND)},
        'sha256': {'abc': sha256(abc_path), 'npz': sha256(OUT / 'Ellie_Patrol_CaptureGroom_curves.npz'), 'blend': sha256(OUT_BLEND)},
        'limitations': [
            'Reconstructed fibers follow original polygonal card geometry and opacity atlases. These are not recovered original artist strand curves.',
            'Opacity quantile transport infers the strands within each card. Fully opaque thick atlas areas do not reveal buried individual fibers.',
            'Each source UV island remains independent; scalp endpoint proximity orients roots but does not recover anatomical follicles or hidden original guides.',
            'Static captured-pose groom only; no skeletal binding, dynamics, original hair simulation or animated deformation is claimed.',
            'Blender custom properties are userProperties rather than standard groom arbGeomParams. Native Alembic group metadata postprocess and actual UE hair_groups_info must validate imported groups.',
            'Raw Blender5.2 Alembic contains eight OCurves shapes / 105908 curves, twice the unique source. Independent native reader confirmed actual duplicate shapes; canonical native Grouped archive removes only bitwise-equal arrays with identity transforms.'
        ], 'verification_elapsed_seconds': time.time() - started,
    }
    attach_native_canonical(manifest)
    (OUT / 'groom_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('GROOM_FINALIZED', json.dumps({k: manifest[k] for k in ('curve_count', 'point_count', 'bounds_ue_cm')}), flush=True)


def main():
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    source_scene = bpy.context.scene
    source_scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    scalp = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('SM_patrol_hair_base_'))
    evaluated = scalp.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    scalp_verts = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    scalp_polys = [tuple(p.vertices) for p in mesh.polygons]
    scalp_bvh = BVHTree.FromPolygons(scalp_verts, scalp_polys)
    evaluated.to_mesh_clear()
    def scalp_distance(p):
        found = scalp_bvh.find_nearest(Vector(p))
        return float(found[3]) if found[0] is not None else math.inf

    source_objects = [o for o in bpy.data.objects if o.type == 'MESH' and object_group(o)]
    groups = {g: [] for g in GROUP_IDS}
    input_report = []
    cached_images = {}
    for obj in sorted(source_objects, key=lambda o: o.name):
        group = object_group(obj)
        material = obj.data.materials[0]
        image = next(n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and 'Opacity' in n.name)
        if image.name not in cached_images:
            cached_images[image.name] = image_array(image)
        opacity = cached_images[image.name]
        islands = evaluated_islands(obj, depsgraph, opacity)
        for island in islands:
            island['opacity'] = opacity
        groups[group].extend(islands)
        input_report.append({'object': obj.name, 'group': group, 'material': material.name,
                             'opacity_image': bpy.path.abspath(image.filepath), 'opacity_resolution': list(image.size),
                             'evaluated_uv_islands': len(islands), 'vertices': len(obj.data.vertices), 'triangles': len(obj.data.polygons),
                             'capture_affine_corrective': float(obj.data.shape_keys.key_blocks['CaptureAffineCorrective'].value) if obj.data.shape_keys and 'CaptureAffineCorrective' in obj.data.shape_keys.key_blocks else None})
        print('GROOM_ISLANDS', obj.name, len(islands), flush=True)

    rng = np.random.default_rng(SEED)
    all_curves, all_group_ids, all_widths, all_root_uv = [], [], [], []
    source_indices, all_island_indices = [], []
    object_names = [r['object'] for r in input_report]
    group_report, island_report = [], []
    collection = bpy.data.collections.new('Ellie_Captured_Groom_Strands')
    source_scene.collection.children.link(collection)
    groom_objects = []
    for group, islands in groups.items():
        weights = np.array([i['weight'] for i in islands])
        if not len(weights) or weights.sum() == 0:
            raise RuntimeError('No usable source islands for ' + group)
        allocation = np.floor(weights / weights.sum() * TARGETS[group]).astype(int)
        allocation += (allocation < 2) * 2
        curves, records = [], []
        for island, count in zip(islands, allocation):
            generated, metadata = make_strands(island, int(count), rng, scalp_distance, group)
            curves.extend(generated)
            records.extend(metadata)
            island_report.append({'object': island['object'], 'island': island['index'], 'group': group,
                                  'area_m2': island['area_m2'], 'mean_opacity': island['coverage'],
                                  'uv_min': island['uv_min'], 'uv_max': island['uv_max'],
                                  'requested': int(count), 'accepted': len(generated)})
        if not curves:
            raise RuntimeError('No curves generated for ' + group)
        curves = np.array(curves, dtype=np.float32)
        widths = rng.uniform(.05, .08, len(curves)).astype(np.float32)
        if group == 'flyaway':
            widths *= .85
        material = hair_material(group)
        obj = create_curve_object('Groom_Ellie_' + group, curves, widths, material, collection, GROUP_IDS[group])
        groom_objects.append(obj)
        all_curves.append(curves)
        all_group_ids.extend([GROUP_IDS[group]] * len(curves))
        all_widths.extend(widths)
        all_root_uv.extend([r[2] for r in records])
        source_indices.extend([object_names.index(r[0]) for r in records])
        all_island_indices.extend([r[1] for r in records])
        lengths = [r[4] for r in records]
        roots, tips = [r[5] for r in records], [r[6] for r in records]
        group_report.append({'name': group, 'group_id': GROUP_IDS[group], 'curve_count': len(curves), 'point_count': len(curves) * POINTS,
                             'source_islands': len(islands), 'length_cm_min_median_max': (np.percentile(lengths, [0, 50, 100]) * 100).tolist(),
                             'root_scalp_distance_cm_median_p95': (np.percentile(roots, [50, 95]) * 100).tolist(),
                             'tip_scalp_distance_cm_median_p95': (np.percentile(tips, [50, 95]) * 100).tolist(),
                             'root_reversed_count': sum(r[3] for r in records),
                             'bounds_ue_cm': [blender_m_to_ue_cm(curves).min((0, 1)).tolist(), blender_m_to_ue_cm(curves).max((0, 1)).tolist()]})
        print('GROOM_GROUP', group, len(curves), flush=True)
    curves_m = np.concatenate(all_curves)
    curves_cm = blender_m_to_ue_cm(curves_m).astype(np.float32)
    group_ids = np.array(all_group_ids, dtype=np.int32)
    widths_mm = np.array(all_widths, dtype=np.float32)
    npz_path = OUT / 'Ellie_Patrol_CaptureGroom_curves.npz'
    np.savez_compressed(npz_path, positions_cm=curves_cm, positions_blender_m=curves_m,
                        curve_vertex_counts=np.full(len(curves_m), POINTS, np.int32), group_ids=group_ids,
                        widths_mm=widths_mm, root_uv=np.array(all_root_uv, np.float32),
                        source_object_index=np.array(source_indices, np.int32),
                        source_island_index=np.array(all_island_indices, np.int32),
                        source_object_names=np.array(object_names), group_names=np.array(list(GROUP_IDS)))
    # Preserve the exact original meshes, modifiers, textures and rig in the new
    # editable scene. Only the replaced visible hair cards are hidden.
    for obj in source_objects:
        obj.hide_render = True
        obj.hide_set(True)
        obj['groom_source_card'] = True
    scalp['groom_scalp_policy'] = 'retained original evaluated base mesh; not reconstructed strands'
    source_scene['groom_reconstruction_manifest'] = str(OUT / 'groom_manifest.json')
    source_scene['groom_source_frame'] = 1
    source_scene['groom_source_blend'] = str(SOURCE)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in groom_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = groom_objects[0]
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

    # Blender's Alembic exporter always writes (x,z,-y). This inverse export
    # transform makes RAW Alembic coordinates exactly UE actor-local cm.
    # The edited .blend above remains in the original Blender meter basis.
    export_scene = bpy.data.scenes.new('Groom_Alembic_UEcm_Export')
    export_scene.frame_start = export_scene.frame_end = 1
    bpy.context.window.scene = export_scene
    export_objects = []
    for group in GROUP_IDS:
        select = group_ids == GROUP_IDS[group]
        ue = curves_cm[select]
        export_points = ue[..., [0, 2, 1]].copy()
        export_points[..., 1] *= -1
        obj = create_curve_object('Groom_Ellie_' + group, export_points, widths_mm[select], None,
                                  export_scene.collection, GROUP_IDS[group], export=True)
        obj.select_set(True)
        export_objects.append(obj)
    bpy.context.view_layer.objects.active = export_objects[0]
    abc_path = OUT / 'Ellie_Patrol_CaptureGroom.abc'
    bpy.ops.wm.alembic_export(filepath=str(abc_path), start=1, end=1, xsamples=1, gsamples=1,
                              selected=True, flatten=False,
                              global_scale=1., export_hair=False, export_particles=False,
                              packuv=False, uvs=False, normals=False, vcolors=False,
                              face_sets=False, curves_as_mesh=False, use_instancing=False,
                              export_custom_properties=True, triangulate=False)
    print('GROOM_ABC_EXPORTED', abc_path, flush=True)
    # Round trip with Blender's inverse Alembic basis. Compare every point, not
    # merely bounding boxes or file existence. This catches unintended scale,
    # axis transforms, lost strands and point order changes.
    roundtrip = verify_alembic(abc_path, curves_cm, group_ids)
    manifest = {
        'source_blend': str(SOURCE), 'source_blend_sha256': sha256(SOURCE),
        'source_capture': 'D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture',
        'source_frame': 1, 'seed': SEED, 'created_by': str(Path(__file__)),
        'method': 'Per evaluated source-card topology/UV island, trace fixed quantiles of sampled opacity mass along atlas V; map each UV to its original triangle by barycentric interpolation; discard transparent gaps/jumps; orient root toward nearest retained scalp triangle; resample equal arclength.',
        'root_method': 'Endpoint nearest original evaluated SM_patrol_hair_base scalp surface; no ellipsoid or generic hairstyle primitive. This is nearest-endpoint orientation, not proof of follicle locations.',
        'editable_blend_basis': 'original Blender actor-local meters; inherited frame1 CaptureAffineCorrective evaluated geometry',
        'abc_axis': 'RAW Alembic positions are Unreal actor-local centimeters (x,-y,z)*100 from Blender source. Export-only precoords (UE.x,-UE.z,UE.y) compensate Blender writer (x,z,-y). UE conversion rotation=(0,0,0), scale=(1,1,1).',
        'alembic_curve_type': 'legacy Blender CURVE, POLY splines, 24 points, one static sample; Blender5.2 raw export requires native exact-array shape deduplication before UE import',
        'curve_count': len(curves_m), 'points_per_curve': POINTS, 'point_count': int(curves_m.shape[0] * POINTS),
        'width_mm_min_max': [float(widths_mm.min()), float(widths_mm.max())],
        'bounds_ue_cm': [curves_cm.min((0, 1)).tolist(), curves_cm.max((0, 1)).tolist()],
        'group_ids': GROUP_IDS, 'groups': group_report, 'inputs': input_report, 'islands': island_report,
        'roundtrip_verification': roundtrip,
        'raw_archive_warning': {'raw_curve_shapes': 8, 'raw_curve_count': len(curves_m) * 2,
                                'unique_reconstructed_curve_count': len(curves_m),
                                'policy': 'Raw Blender5.2 archive is an intermediate; native deduplication/group metadata conversion required before canonical UE import.'},
        'outputs': {'abc': str(abc_path), 'npz': str(npz_path), 'blend': str(OUT_BLEND)},
        'sha256': {'abc': sha256(abc_path), 'npz': sha256(npz_path), 'blend': sha256(OUT_BLEND)},
        'limitations': [
            'Original render assets are polygonal hair cards with opacity atlases, not recovered original artist strand curves. Reconstruction inherits the evaluated captured card silhouette and layers.',
            'Opacity quantile transport infers strand trajectories inside each card; the opaque thick atlas does not encode individual buried fibers. Submillimeter deterministic normal spread separates reconstructed fibers.',
            'Source topology and atlas seams constrain continuity; each island is independent. Hair roots are oriented by scalp proximity, with no anatomical follicle recovery or new simulation.',
            'Static captured-pose groom only. No skeletal binding, motion, dynamics or original guide simulation is claimed.',
            'Blender custom group properties are not standard groom arbGeomParams. Native metadata conversion and exact-array duplicate shape removal are required; NPZ group_ids/root_uv/widths_mm preserve explicit metadata.',
            'Original scalp base mesh is retained in the editable scene as a cap. Original actual hair cards remain hidden and editable for comparison.'
        ], 'elapsed_seconds': time.time() - started,
    }
    attach_native_canonical(manifest)
    (OUT / 'groom_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('GROOM_COMPLETE', json.dumps({k: manifest[k] for k in ('curve_count', 'point_count', 'bounds_ue_cm', 'elapsed_seconds')}), flush=True)


if __name__ == '__main__':
    import sys
    if '--verify-existing' in sys.argv:
        finalize_existing()
    else:
        main()
