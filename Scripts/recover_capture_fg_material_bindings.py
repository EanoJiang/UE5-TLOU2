"""Match original FG GBuffer texture SRVs to dictionary BC mip bytes."""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import re
import struct
import numpy as np
from ngfx_resource_reader import object_blob, read_chunk, read_resource, resource_pages

ROOT = Path('D:/TLOU2_UE5_8_Codex')
CAP = ROOT / 'Exports/CaptureBuffers'
REPORT = ROOT / 'Content/TLOU2/Reports'
TEXTURES = json.loads((ROOT / 'Exports/PlinthTexturesDecoded/texture_decode_manifest.json').read_text())
SHADERS = {r['chunk_id']: r for r in json.loads((CAP / 'shader_index.json').read_text())['rows']}


@lru_cache(maxsize=128)
def top_texture(uid):
    blob = object_blob(uid)
    for pos in range(max(0, len(blob) - 76)):
        box = struct.unpack_from('<6I', blob, pos)
        size, zero, chunk, chunk_offset, reserved = struct.unpack_from('<5Q', blob, pos + 24)
        if (box[:3] != (0, 0, 0) or box[5] != 1 or not 4 <= box[3] <= 16384
                or not 4 <= box[4] <= 16384 or box[3] & (box[3] - 1) or box[4] & (box[4] - 1)
                or not 0 < chunk <= 47635 or zero or reserved or not 0 < size <= 268435456):
            continue
        payload = read_chunk(chunk)
        if chunk_offset + size > len(payload):
            continue
        data = payload[chunk_offset:chunk_offset + size]
        return {'resource_uid': uid, 'width': box[3], 'height': box[4], 'chunk_id': chunk,
                'state_descriptor_offset': pos, 'bytes': size, 'sha256': hashlib.sha256(data).hexdigest()}
    return None


@lru_cache(maxsize=256)
def dictionary_mip_hash(row_number, target_width, target_height):
    row = TEXTURES[row_number]
    descriptor = row.get('dictionary_descriptor')
    if descriptor is None or row['format'] not in (61, 71, 72, 77, 78, 80, 83, 98, 99):
        return None
    width, height = descriptor['width'], descriptor['height']
    block = 8 if row['format'] in (71, 72, 80) else 16
    offset = 0
    mip = 0
    while width >= target_width and height >= target_height:
        row_bytes = width if row['format'] == 61 else (width + 3) // 4 * block
        pitch = (row_bytes + 255) & ~255
        rows = height if row['format'] == 61 else (height + 3) // 4
        if (width, height) == (target_width, target_height):
            with open(descriptor['source_pak'], 'rb') as stream:
                stream.seek(descriptor['payload_abs'] + offset)
                padded = stream.read(pitch * rows)
            if len(padded) != pitch * rows:
                return None
            data = b''.join(padded[y * pitch:y * pitch + row_bytes] for y in range(rows))
            return hashlib.sha256(data).hexdigest(), mip, offset
        offset = (offset + pitch * rows + 511) & ~511
        width, height = max(1, width // 2), max(1, height // 2)
        mip += 1
    return None


@lru_cache(maxsize=256)
def original_texture(uid):
    recovered = top_texture(uid)
    if recovered is None:
        return {'resource_uid': uid, 'verification': 'no supported captured2D mip payload'}
    matches = []
    for index, row in enumerate(TEXTURES):
        result = dictionary_mip_hash(index, recovered['width'], recovered['height'])
        if result and result[0] == recovered['sha256']:
            matches.append({'texture_name': row['name'], 'decoded_png': row['decoded_path'],
                            'dictionary_source_pak': row['dictionary_descriptor']['source_pak'],
                            'dictionary_payload_abs': row['dictionary_descriptor']['payload_abs'],
                            'dictionary_mip_level': result[1], 'dictionary_mip_payload_offset': result[2],
                            'format': row['format']})
    return {**recovered, 'original_texture_matches': matches,
            'verification': 'bit_exact_original_texture_mip_bytes' if matches else 'captured_mip_not_in_stage_texture_dictionary_selection'}


def cbv_bytes(view, byte_count, byte_offset=0):
    address = view['address'] + byte_offset
    for uid in (5331, 5333, 5335, 5367, 7556):
        base = struct.unpack_from('<Q', object_blob(uid, 'create'), 104)[0]
        length = sum(p['bytes'] for p in resource_pages(uid))
        if base <= address and address + byte_count <= base + length:
            return {'resource_uid': uid, 'resource_offset': address - base}, read_resource(uid, address - base, byte_count)
    raise ValueError(('unresolved material CBV', address, byte_count))


def main():
    actual = json.loads((CAP / 'fg_stage_index_draw_matches.json').read_text())
    rows = []
    used = set()
    for draw in actual:
        name = draw['source_name']
        if name in used or draw['pipeline_uid'] is None:
            continue
        create = object_blob(draw['pipeline_uid'], 'create')
        if len(create) < 775:
            continue
        pixel_chunk = struct.unpack_from('<Q', create, 767)[0]
        shader = SHADERS.get(pixel_chunk)
        if shader is None or shader.get('entry_name') != 'MainPsGBuffer__Wrp':
            continue
        slots = draw.get('tables', {}).get('9', {}).get('slots', [])
        ir = Path(shader['disassembly']).read_text()
        registers = sorted({int(x) for x in re.findall(r'\bT\d+\s+t(\d+),space5\s+1\b', ir)})
        textures = []
        for register in registers:
            if register >= len(slots) or slots[register] is None:
                textures.append({'shader_register': register, 'verification': 'unresolved descriptor'})
                continue
            view = slots[register]
            if view.get('kind') != 'SRV' or view.get('dimension', 4) != 4:
                textures.append({'shader_register': register, 'view': view, 'verification': 'non2D SRV'})
                continue
            textures.append({'shader_register': register, 'srv_format': view['format'], **original_texture(view['resource_uid'])})
        rows.append({'source_submesh': name, 'source_material': draw['source_material'],
                     'sequence': draw['sequence'], 'command_index': draw['command_index'],
                     'pipeline_uid': draw['pipeline_uid'], 'pixel_shader_chunk': pixel_chunk,
                     'original_pixel_shader': shader['disassembly'], 'textures': textures})
        used.add(name)
    depth_rows = []
    used_depth = set()
    for draw in actual:
        if draw['source_name'] in used_depth or draw['pipeline_uid'] is None:
            continue
        create = object_blob(draw['pipeline_uid'], 'create')
        if len(create) < 775:
            continue
        pixel_chunk = struct.unpack_from('<Q', create, 767)[0]
        shader = SHADERS.get(pixel_chunk)
        if shader is None or shader.get('entry_name') != 'MainPsDepthOnlyObjId__Wrp':
            continue
        ir = Path(shader['disassembly']).read_text()
        registers = sorted({int(x) for x in re.findall(r'\bT\d+\s+t(\d+),space5\s+1\b', ir)})
        if not registers:
            continue
        slots = draw.get('tables', {}).get('9', {}).get('slots', [])
        textures = [{'shader_register': register, **original_texture(slots[register]['resource_uid'])}
                    for register in registers if register < len(slots) and slots[register]]
        row = {'source_submesh': draw['source_name'], 'source_material': draw['source_material'],
               'sequence': draw['sequence'], 'command_index': draw['command_index'],
               'pipeline_uid': draw['pipeline_uid'], 'pixel_shader_chunk': pixel_chunk,
               'original_pixel_shader': shader['disassembly'], 'textures': textures}
        if pixel_chunk in (47518, 47544, 47510):
            material_source, material = cbv_bytes(draw['tables']['3']['slots'][2], 64)
            global_source, global_values = cbv_bytes(draw['tables']['3']['slots'][0], 16, 55 * 16)
            values = np.frombuffer(material, '<f4').reshape(4, 4)
            bias = float(np.frombuffer(global_values, '<f4')[2])
            if pixel_chunk in (47518, 47544):
                base, factor = float(values[0, 3]), float(values[1, 0])
                parameter_registers = 'base=material reg0.w; distanceFactor=reg1.x'
            else:
                base, factor = float(values[2, 2]), float(values[2, 3])
                parameter_registers = 'base=material reg2.z; distanceFactor=reg2.w'
            row.update(opacity_material_source=material_source,
                       opacity_material_first4_float4=values.tolist(),
                       global_opacity_bias_source=global_source, global_opacity_bias=bias,
                       base_opacity_threshold=base, distance_sqrt_factor=factor,
                       shader_parameter_registers=parameter_registers,
                       exact_keep_formula='saturate(mask.R + globalBias) > max(baseThreshold / max(1,distanceFactor*sqrt(cameraDistanceMeters)),1e-7) - 1e-7',
                       ue_masked_equivalent='OpacityMask=saturate(mask.R+globalBias)*max(1,distanceFactor*sqrt(Distance(AbsoluteWorldPosition,CameraPosition)/100))*(0.5/baseThreshold); OpacityMaskClipValue=0.5',
                       distance3m_threshold=base / max(1, factor * np.sqrt(3)),
                       distance4m_threshold=base / max(1, factor * np.sqrt(4)))
        depth_rows.append(row)
        used_depth.add(draw['source_name'])
    report = {'source_subsets_with_original_GBuffer_texture_binding_map': len(rows),
              'source_subsets_with_sampled_depth_prepass_opacity': len(depth_rows),
              'method': 'Only actual indexed draws whose original pipeline pixel bytecode is MainPsGBuffer__Wrp are selected. Disassembly determines the referenced tN,space5 registers in graphics root9. Initial bound texture resource payloads are matched to source dictionary mips by exact compressed BC bytes after removal of original PC upload row padding. Depth-only draw residual texture descriptors are intentionally excluded.',
              'opacity_scope': 'GBuffer shaders may omit opacity sampling because the depth prepass already masks the surface. The depth_prepass_opacity rows independently prove the bound opacity texture and clipping shader. Absence from GBuffer texture declarations does not establish opaque rendering or color-alpha masking.',
              'rows': rows, 'depth_prepass_opacity': depth_rows}
    path = REPORT / 'CAPTURE_FG_STAGE_MATERIAL_TEXTURE_BINDINGS.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('MATERIAL_SUBSETS', len(rows))
    print('DEPTH_PREPASS_OPACITY', [(r['source_submesh'], r['pixel_shader_chunk'], r.get('base_opacity_threshold'), r.get('distance_sqrt_factor')) for r in depth_rows])
    for row in rows:
        if row['source_submesh'] in ('groundShape_shader7_merged_partition0', 'fernShape_shader8_merged_partition0', 'baseShape_shader11_merged_partition0', 'leavesShape_shader6_merged_partition0', 'rocksShape_shader10_merged_partition0'):
            print(row['source_submesh'], [(t['shader_register'], [m['texture_name'] for m in t.get('original_texture_matches', [])]) for t in row['textures']])


if __name__ == '__main__':
    main()
