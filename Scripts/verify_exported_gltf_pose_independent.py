"""Evaluate exported GLB bytes independently of Blender and UE skinning.

Apply the captured armature clip's first sample, default morph POSITION deltas,
joint globals, inverse binds, and every JOINTS_n/WEIGHTS_n set. Compare each
exported mesh separately with its original PAK/GPU reference in game axes/meters.
The glTF exporter reverses Blender's game-to-Blender basis conversion, so these
glTF world coordinates directly match the actor-local game reference coordinates.
Original triangle indices identify drawable source vertices; allocated orphan
vertices are reported separately because interchange exporters omit them.
Original drawable triangle multiplicity and winding are checked using ordered
base positions or canonical coordinate/influence signatures after reordering.
Normals, tangents, materials, later samples and GPU rounding remain outside scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
DTYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load_glb(path):
    raw = path.read_bytes()
    magic, version, size = struct.unpack_from("<4sII", raw)
    assert magic == b"glTF" and version == 2 and size == len(raw)
    chunks = {}
    offset = 12
    while offset < size:
        length, kind = struct.unpack_from("<II", raw, offset)
        assert offset + 8 + length <= size
        chunks[kind] = raw[offset + 8:offset + 8 + length]
        offset += 8 + length
    return raw, json.loads(chunks[0x4E4F534A]), chunks[0x004E4942]


def accessor(doc, binary, index):
    entry = doc["accessors"][index]
    dtype = np.dtype(DTYPES[entry["componentType"]])
    components = COMPONENTS[entry["type"]]
    if "bufferView" in entry:
        view = doc["bufferViews"][entry["bufferView"]]
        assert view.get("buffer", 0) == 0
        start = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
        stride = view.get("byteStride", dtype.itemsize * components)
        end = start + max(entry["count"] - 1, 0) * stride + dtype.itemsize * components
        assert end <= view.get("byteOffset", 0) + view["byteLength"] <= len(binary)
        result = np.ndarray((entry["count"], components), dtype=dtype, buffer=binary,
                            offset=start, strides=(stride, dtype.itemsize)).copy()
    else:
        result = np.zeros((entry["count"], components), dtype=dtype)
    if "sparse" in entry:
        sparse = entry["sparse"]
        indices = sparse["indices"]
        view = doc["bufferViews"][indices["bufferView"]]
        ids = np.frombuffer(binary, dtype=DTYPES[indices["componentType"]],
                            count=sparse["count"],
                            offset=view.get("byteOffset", 0) + indices.get("byteOffset", 0))
        values = sparse["values"]
        view = doc["bufferViews"][values["bufferView"]]
        data = np.frombuffer(binary, dtype=dtype, count=sparse["count"] * components,
                             offset=view.get("byteOffset", 0) + values.get("byteOffset", 0))
        assert np.all(ids < len(result)) and len(np.unique(ids)) == len(ids)
        result[ids] = data.reshape(-1, components)
    if entry.get("normalized") and entry["componentType"] != 5126:
        result = result.astype(np.float64) / np.iinfo(dtype).max
        if np.issubdtype(dtype, np.signedinteger):
            result = np.maximum(result, -1)
    assert np.isfinite(result).all()
    return result


def node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    assert abs(x*x + y*y + z*z + w*w - 1) < 1e-4
    matrix = np.eye(4)
    matrix[:3, :3] = np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ]) @ np.diag(node.get("scale", [1, 1, 1]))
    matrix[:3, 3] = node.get("translation", [0, 0, 0])
    return matrix


def distances(actual, expected):
    assert len(actual) and len(expected) and np.isfinite(actual).all() and np.isfinite(expected).all()
    forward = cKDTree(expected).query(actual)[0]
    reverse = cKDTree(actual).query(expected)[0]
    return {"export_to_source_max_m": float(forward.max()),
            "source_to_export_max_m": float(reverse.max()),
            "bidirectional_max_m": float(max(forward.max(), reverse.max())),
            "export_to_source_mean_m": float(forward.mean()),
            "source_to_export_mean_m": float(reverse.mean())}


def canonical_triangle(triangle):
    a, b, c = (int(x) for x in triangle)
    return min((a, b, c), (b, c, a), (c, a, b))


def triangle_topology(source_positions, source_indices, source_ids, source_weights,
                      export_positions, export_indices, export_ids, export_weights):
    source_faces = source_indices.reshape(-1, 3)
    export_faces = export_indices.reshape(-1, 3)
    expected_corners = source_positions[source_indices]
    actual_corners = export_positions[export_indices]
    same_shape = expected_corners.shape == actual_corners.shape
    ordered_error = float(np.max(np.abs(actual_corners - expected_corners))) if same_shape else None
    ordered_pass = same_shape and ordered_error < 1e-7
    out = {"source_triangles": len(source_faces), "export_triangles": len(export_faces),
           "ordered_triangle_base_position_max_error_m": ordered_error,
           "source_exact_repeated_index_triangles": len(source_faces) - len(set(map(tuple, source_faces))),
           "ordered_triangle_base_positions_match": ordered_pass,
           "base_position_tolerance_m": 1e-7}
    if ordered_pass:
        out.update({"method": "Original ordered triangle-corner position sequence under static mesh-node transforms; winding, count and multiplicity retained.",
                    "missing_triangle_copies": 0, "extra_triangle_copies": 0,
                    "missing_unique_drawable_triangle_signatures": 0,
                    "geometric_surface_coverage_pass": True, "pass": True})
        return out

    def weights_by_bone(ids, weights):
        result = {}
        for bone, weight in zip(ids, weights):
            if weight > 0:
                result[int(bone)] = result.get(int(bone), 0.0) + float(weight)
        return result

    source_bindings = [weights_by_bone(ids, weights) for ids, weights in zip(source_ids, source_weights)]
    source_keys = {}
    source_canonical = []
    for position, binding in zip(source_positions, source_bindings):
        key = (tuple(float(x) for x in position), tuple(sorted(binding.items())))
        source_canonical.append(source_keys.setdefault(key, len(source_keys)))
    source_canonical = np.array(source_canonical)
    candidate_rows = cKDTree(source_positions).query_ball_point(export_positions, 1e-7)
    exported_canonical = []
    maximum_binding_error = maximum_position_error = 0.0
    for position, ids, weights, candidates in zip(export_positions, export_ids, export_weights, candidate_rows):
        assert candidates, "an exported base position has no original source vertex"
        binding = weights_by_bone(ids, weights)
        errors = [max((abs(binding.get(bone, 0) - source_bindings[candidate].get(bone, 0))
                       for bone in binding.keys() | source_bindings[candidate].keys()), default=0.0)
                  for candidate in candidates]
        best = int(np.argmin(errors))
        source_vertex = candidates[best]
        maximum_binding_error = max(maximum_binding_error, errors[best])
        maximum_position_error = max(maximum_position_error, float(np.linalg.norm(position - source_positions[source_vertex])))
        exported_canonical.append(source_canonical[source_vertex])
    exported_canonical = np.array(exported_canonical)
    expected = Counter(canonical_triangle(face) for face in source_canonical[source_faces])
    actual = Counter(canonical_triangle(face) for face in exported_canonical[export_faces])
    missing, extra = expected - actual, actual - expected
    missing_unique = sum(actual[triangle] == 0 for triangle in missing)
    out.update({"method": "Canonical oriented triangle multiset from exact source base coordinates and named bone influences; export seam vertices map to source coordinates/bindings before cyclic corner normalization.",
                "source_vertex_mapping_max_position_error_m": maximum_position_error,
                "source_vertex_mapping_max_weight_error": maximum_binding_error,
                "weight_mapping_tolerance": 2e-6,
                "missing_triangle_copies": sum(missing.values()), "extra_triangle_copies": sum(extra.values()),
                "missing_unique_drawable_triangle_signatures": missing_unique,
                "missing_triangle_signatures_still_drawn": len(missing) - missing_unique,
                "source_influence_mapping_within_2e6": maximum_binding_error < 2e-6,
                "geometric_surface_coverage_pass": missing_unique == 0 and not extra,
                "pass": not missing and not extra and maximum_binding_error < 2e-6})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", type=Path, default=ROOT/"Exports/Ellie_Patrol_CapturedSkinPose.glb")
    parser.add_argument("--reference", type=Path, default=ROOT/"Exports/CaptureBuffers/IndependentSkinnedMeshes/selected29_independent_skinning_report.json")
    parser.add_argument("--manifest", type=Path, default=ROOT/"Exports/captured_skin_pose_chunk_manifest.json")
    parser.add_argument("--animation", default="AN_CapturedSkinPose_Frame5445")
    parser.add_argument("--tolerance-m", type=float, default=0.0001)
    parser.add_argument("--output", type=Path, default=ROOT/"Exports/captured_gltf_independent_pose_validation.json")
    args = parser.parse_args()
    raw, doc, binary = load_glb(args.glb)
    reference_raw = args.reference.read_bytes()
    references = json.loads(reference_raw)["rows"]
    manifest = json.loads(args.manifest.read_text())
    rig_rows = json.loads((ROOT/"Exports/Ellie_AugmentedBindRest_SourceMatrices.json").read_text())["rows"]
    bone_id_by_name = {r["bone_name"]: r["bone_index"] for r in rig_rows}
    human_ids = np.array([r["bone_index"] for r in rig_rows if r.get("rig_owner") not in ("hoodie", "backpack")])
    hoodie_rows = sorted((r for r in rig_rows if r.get("rig_owner") == "hoodie"), key=lambda r: r["owned_source_bone_index"])
    hoodie_ids = np.array([r["bone_index"] for r in hoodie_rows])
    chunk_by_node = {m["source_mesh"]: chunk for chunk, entry in manifest["chunks"].items() for m in entry["meshes"]}
    nodes = [dict(node) for node in doc["nodes"]]
    animations = [a for a in doc.get("animations", []) if a.get("name") == args.animation]
    assert len(animations) == 1, "requested armature clip must exist exactly once"
    animation = animations[0]
    times = []
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        assert sampler.get("interpolation", "LINEAR") in ("LINEAR", "STEP")
        times.append(float(accessor(doc, binary, sampler["input"])[0, 0]))
        target = channel["target"]
        assert target["path"] in ("translation", "rotation", "scale"), "armature clip must use TRS channels"
        assert "matrix" not in nodes[target["node"]]
        nodes[target["node"]][target["path"]] = accessor(doc, binary, sampler["output"])[0].tolist()
    assert times and max(times) == min(times), "all evaluated channels must share the first sample time"
    parents = {}
    for index, node in enumerate(nodes):
        for child in node.get("children", []):
            assert child not in parents
            parents[child] = index
    globals_ = {}
    static_globals = {}
    visiting = set()

    def global_matrix(index):
        if index not in globals_:
            assert index not in visiting, "node hierarchy contains a cycle"
            visiting.add(index)
            globals_[index] = (global_matrix(parents[index]) if index in parents else np.eye(4)) @ node_matrix(nodes[index])
            visiting.remove(index)
        return globals_[index]

    def static_global_matrix(index):
        if index not in static_globals:
            static_globals[index] = (static_global_matrix(parents[index]) if index in parents else np.eye(4)) @ node_matrix(doc["nodes"][index])
        return static_globals[index]

    rows = []
    matched_sources = set()
    matched_nodes = set()
    for node_index, node in enumerate(nodes):
        if "mesh" not in node or "skin" not in node:
            continue
        node_name = node["name"]
        assert node_name.startswith("SM_") and node_name in chunk_by_node
        # Blender limits object names to 63 characters. Fail on ambiguous prefixes.
        source_name = node_name[3:]
        matches = [r for r in references if r["source_mesh"].startswith(source_name)]
        assert len(matches) == 1, (node_name, [r["source_mesh"] for r in matches])
        source = matches[0]
        source_key = (source["source_pak"], source["source_mesh"])
        assert source_key not in matched_sources and node_name not in matched_nodes
        matched_sources.add(source_key)
        matched_nodes.add(node_name)
        mesh = doc["meshes"][node["mesh"]]
        skin = doc["skins"][node["skin"]]
        binds = accessor(doc, binary, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        assert len(binds) == len(skin["joints"])
        # glTF world-space skin = sum(weight * jointGlobal * inverseBind * point).
        matrices = np.array([global_matrix(i) for i in skin["joints"]]) @ binds
        joint_named_ids = np.array([bone_id_by_name[doc["nodes"][i]["name"]] for i in skin["joints"]])
        target_names = mesh.get("extras", {}).get("targetNames", [])
        morph_weights = node.get("weights", mesh.get("weights", []))
        assert target_names == ["CaptureAffineCorrective"] and morph_weights == [1], node_name
        points = []
        topology_positions = []
        topology_indices = []
        topology_ids = []
        topology_weights = []
        vertex_offset = 0
        maximum_influences = 0
        maximum_sum_error = 0.0
        for primitive in mesh["primitives"]:
            attrs = primitive["attributes"]
            positions = accessor(doc, binary, attrs["POSITION"]).astype(np.float64)
            base_positions = (static_global_matrix(node_index) @ np.column_stack([positions, np.ones(len(positions))]).T).T[:, :3]
            assert primitive.get("mode", 4) == 4, "exported source meshes must remain triangle lists"
            triangle_indices = accessor(doc, binary, primitive["indices"]).ravel() if "indices" in primitive else np.arange(len(positions))
            assert len(triangle_indices) % 3 == 0 and (triangle_indices < len(positions)).all()
            topology_positions.append(base_positions)
            topology_indices.append(triangle_indices + vertex_offset)
            primitive_ids = []
            primitive_weights = []
            assert len(primitive.get("targets", [])) == len(morph_weights)
            for weight, target in zip(morph_weights, primitive["targets"]):
                if "POSITION" in target:
                    positions += weight * accessor(doc, binary, target["POSITION"])
            homogeneous = np.column_stack([positions, np.ones(len(positions))])
            result = np.zeros((len(positions), 3))
            sums = np.zeros(len(positions))
            influences = np.zeros(len(positions), dtype=np.int32)
            joint_keys = sorted(k for k in attrs if k.startswith("JOINTS_"))
            assert joint_keys
            for key in joint_keys:
                index = key.split("_")[1]
                joints = accessor(doc, binary, attrs[key])
                weights = accessor(doc, binary, attrs["WEIGHTS_" + index])
                assert joints.shape == weights.shape == (len(positions), 4)
                assert np.issubdtype(joints.dtype, np.integer) and (joints < len(matrices)).all() and (joints >= 0).all()
                assert (weights >= 0).all()
                primitive_ids.append(joint_named_ids[joints])
                primitive_weights.append(weights)
                result += np.einsum("nijk,nk,ni->nj", matrices[joints][:, :, :3, :], homogeneous, weights)
                sums += weights.sum(axis=1)
                influences += (weights > 0).sum(axis=1)
            maximum_influences = max(maximum_influences, int(influences.max()))
            maximum_sum_error = max(maximum_sum_error, float(np.abs(sums - 1).max()))
            points.append(result)
            topology_ids.append(np.concatenate(primitive_ids, axis=1))
            topology_weights.append(np.concatenate(primitive_weights, axis=1))
            vertex_offset += len(positions)
        actual = np.concatenate(points)
        with np.load(source["path"]) as archive:
            expected = archive["captured_skinned_actor_vertices_game"]
            shader = archive["original_shader_weight_skinned_actor_vertices_game"]
            source_local_ids = archive["source_bone_indices"]
            source_normalized_weights = archive["normalized_source_weights"]
        assert len(expected) == len(shader) == source["vertices"]
        source_raw = Path(source["source_npz"]).read_bytes()
        assert hashlib.sha256(source_raw).hexdigest() == source["source_npz_sha256"]
        source_doc = json.loads(Path(source["source_capture"]).read_text())
        source_mesh = next(m for m in source_doc["meshes"] if m["name"] == source["source_mesh"])
        assert source_mesh["index_type"] in (4, 5)
        with np.load(source["source_npz"]) as archive:
            indices = archive["indices_raw"].view("<u2" if source_mesh["index_type"] == 4 else "<u4")[:source_mesh["count"]]
            stride = source_mesh["bindings"]["pos"]["stride"] // 4
            source_positions = archive["pos_raw"].view("<f4")[:source["vertices"] * stride].reshape(source["vertices"], stride)[:, :3].astype(np.float64)
        assert len(indices) == source_mesh["count"] and len(indices) % 3 == 0
        assert (indices < len(expected)).all()
        referenced = np.unique(indices)
        normalized_metrics = distances(actual, expected[referenced])
        shader_metrics = distances(actual, shader[referenced])
        allocated_metrics = distances(actual, expected)
        allocated_shader_metrics = distances(actual, shader)
        source_named_ids = (hoodie_ids if source["joint_palette_owner"] == "hoodie_owned78" else human_ids)[source_local_ids]
        topology = triangle_topology(source_positions, indices, source_named_ids, source_normalized_weights,
                                     np.concatenate(topology_positions), np.concatenate(topology_indices),
                                     np.concatenate(topology_ids), np.concatenate(topology_weights))
        deformation_pass = maximum_sum_error < 2e-6 and max(normalized_metrics["bidirectional_max_m"], shader_metrics["bidirectional_max_m"]) < args.tolerance_m
        rows.append({"node": node_name, "source_mesh": source["source_mesh"], "source_pak": source["source_pak"],
                     "chunk": chunk_by_node[node_name], "reference_npz": source["path"],
                     "reference_vertices": len(expected), "export_vertices": len(actual),
                     "source_referenced_vertices": len(referenced), "source_unreferenced_vertices": len(expected) - len(referenced),
                     "source_original_triangle_indices": len(indices), "original_source_npz_sha256_matches": True,
                     "skin_joints": len(skin["joints"]), "maximum_active_influences": maximum_influences,
                     "weight_sum_max_error": maximum_sum_error,
                     "morphs": dict(zip(target_names, morph_weights)),
                     "normalized_reference": normalized_metrics, "original_shader_weight_reference": shader_metrics,
                     "allocated_buffer_normalized_reference_diagnostic": allocated_metrics,
                     "allocated_buffer_original_shader_weight_reference_diagnostic": allocated_shader_metrics,
                     "topology": topology, "deformation_pass": deformation_pass,
                     "pass": deformation_pass and topology["pass"]})
    assert matched_nodes == set(chunk_by_node), "exported mesh identities differ from the authoritative chunk manifest"
    assert matched_sources == {(r["source_pak"], r["source_mesh"]) for r in references}, "source reference selection is incomplete"
    report = {"glb": str(args.glb.resolve()), "glb_sha256": hashlib.sha256(raw).hexdigest(),
              "reference": str(args.reference.resolve()), "reference_sha256": hashlib.sha256(reference_raw).hexdigest(),
              "chunk_manifest": str(args.manifest.resolve()), "animation": args.animation, "sample_time_s": times[0],
              "mesh_count": len(rows), "source_vertices": sum(r["reference_vertices"] for r in rows),
              "source_referenced_surface_vertices": sum(r["source_referenced_vertices"] for r in rows),
              "source_unreferenced_buffer_vertices": sum(r["source_unreferenced_vertices"] for r in rows),
              "export_vertices": sum(r["export_vertices"] for r in rows),
              "source_triangles": sum(r["topology"]["source_triangles"] for r in rows),
              "export_triangles": sum(r["topology"]["export_triangles"] for r in rows),
              "missing_triangle_copies": sum(r["topology"]["missing_triangle_copies"] for r in rows),
              "extra_triangle_copies": sum(r["topology"]["extra_triangle_copies"] for r in rows),
              "topology_pass": all(r["topology"]["pass"] for r in rows),
              "geometric_surface_coverage_pass": all(r["topology"]["geometric_surface_coverage_pass"] for r in rows),
              "deformation_pass": all(r["deformation_pass"] for r in rows),
              "normalized_bidirectional_max_m": max(r["normalized_reference"]["bidirectional_max_m"] for r in rows),
              "original_shader_weight_bidirectional_max_m": max(r["original_shader_weight_reference"]["bidirectional_max_m"] for r in rows),
              "allocated_buffer_normalized_bidirectional_max_m_diagnostic": max(r["allocated_buffer_normalized_reference_diagnostic"]["bidirectional_max_m"] for r in rows),
              "tolerance_m": args.tolerance_m, "pass": all(r["pass"] for r in rows),
              "method": "Independent GLB binary accessor/TRS/inverse-bind/morph/all-weight-set evaluation; bidirectional nearest distances against original triangle-referenced vertices within each uniquely matched source mesh, never across meshes.",
              "coordinate_policy": "glTF world game XYZ meters compared with actor-local original PAK/GPU references; Blender basis conversion cancels on glTF export.",
              "count_policy": "Original triangle indices distinguish drawable vertices from unused buffer allocation; the two head partitions contain 592 unused vertices. glTF may omit those and split/deduplicate drawable vertices. Enforce every mesh identity and per-mesh drawable coverage; full allocated-buffer distances remain diagnostic.",
              "scope": "First captured bone sample/default morph deformation and original base-position triangle multiplicity/winding. Normals, materials, later samples and original GPU rounding order remain unverified.",
              "export_weight_filter_note": "Stock Blender glTF exporters tested in4.5.10 and5.2.0 filter weights at0.0001 and validate away duplicate faces. Task-isolated fidelity copies set min_influence0.0 and skip destructive mesh validation. Final5.2 provenance/backups are recorded in Exports/portable_gltf_fidelity_exporter_blender52.json; the earlier4.5 record is retained separately. This validator checks actual exported geometry independently of those declarations.",
              "rows": rows}
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
    if not report["pass"]:
        raise RuntimeError("Exported captured GLB differs from original source deformation or drawable triangle topology")


if __name__ == "__main__":
    main()
