"""Inspect actual exported glTF bytes, hierarchy, inverse binds and all weights."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('glb', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
raw = args.glb.read_bytes()
magic, version, size = struct.unpack_from('<4sII', raw)
assert magic == b'glTF' and version == 2 and size == len(raw), 'invalid GLB header'
offset = 12
chunks = {}
while offset < size:
    length, kind = struct.unpack_from('<II', raw, offset)
    assert offset+8+length <= size
    chunks[kind] = raw[offset+8:offset+8+length]
    offset += 8+length
doc = json.loads(chunks[0x4e4f534a])
binary = chunks[0x004e4942]
fmt = {5120:'b', 5121:'B', 5122:'h', 5123:'H', 5125:'I', 5126:'f'}
components = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4, 'MAT4':16}

def accessor(index):
    ac = doc['accessors'][index]
    bv = doc['bufferViews'][ac['bufferView']]
    count = components[ac['type']]
    unpack = struct.Struct('<'+fmt[ac['componentType']]*count)
    stride = bv.get('byteStride', unpack.size)
    begin = bv.get('byteOffset', 0)+ac.get('byteOffset', 0)
    assert begin+(ac['count']-1)*stride+unpack.size <= bv.get('byteOffset', 0)+bv['byteLength']
    data = [unpack.unpack_from(binary, begin+i*stride) for i in range(ac['count'])]
    if ac.get('normalized') and ac['componentType'] != 5126:
        maximum = {5121:255, 5123:65535, 5120:127, 5122:32767}[ac['componentType']]
        data = [tuple(max(-1.0,v/maximum) for v in row) for row in data]
    return data

identity = ((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))
def mul(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)) for i in range(4))
def node_matrix(node):
    if 'matrix' in node:
        a = node['matrix']
        return tuple(tuple(a[j*4+i] for j in range(4)) for i in range(4))
    x,y,z,w = node.get('rotation', (0,0,0,1))
    s = node.get('scale', (1,1,1))
    t = node.get('translation', (0,0,0))
    r = ((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
         (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
         (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
    return tuple(tuple(r[i][j]*s[j] for j in range(3))+(t[i],) for i in range(3))+((0,0,0,1),)

parents = {}
for i,node in enumerate(doc['nodes']):
    for child in node.get('children', []):
        assert child not in parents, 'multiple node parents'
        parents[child] = i
globals_ = {}
visiting = set()
def global_matrix(index):
    if index in globals_: return globals_[index]
    assert index not in visiting, 'node cycle'
    visiting.add(index)
    local = node_matrix(doc['nodes'][index])
    globals_[index] = mul(global_matrix(parents[index]), local) if index in parents else local
    visiting.remove(index)
    return globals_[index]

skin_reports = []
for index,skin in enumerate(doc['skins']):
    binds = accessor(skin['inverseBindMatrices'])
    assert len(binds) == len(skin['joints'])
    maximum = 0.0
    for joint,data in zip(skin['joints'], binds):
        inverse = tuple(tuple(data[j*4+i] for j in range(4)) for i in range(4))
        closure = mul(global_matrix(joint), inverse)
        maximum = max(maximum, max(abs(closure[i][j]-identity[i][j]) for i in range(4) for j in range(4)))
    skin_reports.append({'skin':index, 'joints':len(skin['joints']), 'rest_inverse_bind_closure_max_error':maximum})

mesh_reports = []
for node in doc['nodes']:
    if 'mesh' not in node or 'skin' not in node: continue
    skin = doc['skins'][node['skin']]
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        attrs = primitive['attributes']
        pos = accessor(attrs['POSITION'])
        joints = [accessor(attrs[f'JOINTS_{i}']) for i in range(8) if f'JOINTS_{i}' in attrs]
        weights = [accessor(attrs[f'WEIGHTS_{i}']) for i in range(8) if f'WEIGHTS_{i}' in attrs]
        assert len(joints) == len(weights) > 0
        assert all(len(a)==len(pos) for a in joints+weights)
        max_count = 0
        max_sum_error = 0.0
        for v in range(len(pos)):
            assert all(math.isfinite(x) for x in pos[v])
            total = 0.0
            active = 0
            for js,ws in zip(joints,weights):
                for j,w in zip(js[v],ws[v]):
                    assert 0 <= j < len(skin['joints']), 'joint outside this skin palette'
                    assert math.isfinite(w) and w >= 0, 'invalid skin weight'
                    total += w
                    active += w > 0
            max_count = max(max_count, active)
            max_sum_error = max(max_sum_error, abs(total-1))
        assert primitive.get('mode',4)==4
        index_count=doc['accessors'][primitive['indices']]['count'] if 'indices' in primitive else len(pos)
        assert index_count%3==0
        mesh_reports.append({'node':node.get('name'), 'vertices':len(pos), 'triangles':index_count//3, 'joint_attribute_sets':len(joints),
                             'max_active_influences':max_count, 'weight_sum_max_error':max_sum_error})
out = {'file':str(args.glb.resolve()), 'file_sha256':hashlib.sha256(raw).hexdigest(), 'file_bytes':size, 'skins':skin_reports, 'meshes':mesh_reports,
       'animation_count':len(doc.get('animations',[])), 'triangles':sum(m['triangles'] for m in mesh_reports),
       'skinned_primitives':len(mesh_reports), 'export_vertices':sum(m['vertices'] for m in mesh_reports),
       'max_active_influences':max(m['max_active_influences'] for m in mesh_reports),
       'weight_sum_max_error':max(m['weight_sum_max_error'] for m in mesh_reports),
       'rest_inverse_bind_closure_max_error':max(s['rest_inverse_bind_closure_max_error'] for s in skin_reports)}
out['pass'] = out['weight_sum_max_error'] < 2e-6 and out['rest_inverse_bind_closure_max_error'] < 1e-4
output = args.output or args.glb.with_name(args.glb.stem+'_gltf_skin_validation.json')
output.write_text(json.dumps(out, indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ('meshes','skins')}, indent=2))
if not out['pass']: raise RuntimeError('glTF skin validation failed')
