"""Hash-bind recovered character uniforms/SRVs and bake portable primary maps.

Original texture PNGs are inputs only. No geometry, Blender, or UE asset writes.
The portable recipe intentionally omits the game's further material layers.
"""
from pathlib import Path
import hashlib
import json
import struct
import numpy as np
from PIL import Image
from ngfx_resource_reader import object_blob, read_resource
import recover_capture_fg_material_bindings as recovery

ROOT = Path('D:/TLOU2_UE5_8_Codex')
REPORT = ROOT / 'Content/TLOU2/Reports'
OUT = ROOT / 'Exports/TexturesDecoded'
EVIDENCE = REPORT / 'ShaderEvidence'
EVIDENCE.mkdir(exist_ok=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def srgb_encode(linear):
    return np.where(linear <= .0031308, 12.92 * linear,
                    1.055 * np.maximum(linear, 0) ** (1 / 2.4) - .055)


def srgb_decode(encoded):
    return np.where(encoded <= .04045, encoded / 12.92,
                    ((encoded + .055) / 1.055) ** 2.4)


def png_array(stem):
    return np.asarray(Image.open(OUT / (stem + '.png')).convert('RGB'), dtype=np.float64) / 255


def save_png(stem, values, space, source, equation):
    target = OUT / (stem + '.png')
    pixels = np.clip(np.rint(values * 255), 0, 255).astype(np.uint8)
    Image.fromarray(pixels).save(target)
    return {'stem': stem, 'path': str(target), 'png_sha256': sha(target),
            'dimensions': [pixels.shape[1], pixels.shape[0]], 'colorspace': space,
            'sources': source, 'equation': equation}


def main():
    # These tests verify actual transfer properties, including clipping and
    # source zero. They do not merely mirror graph construction.
    levels = np.arange(256, dtype=np.float64) / 255
    assert np.max(np.abs(srgb_decode(srgb_encode(levels)) - levels)) < 1e-12
    assert srgb_encode(np.array([0., 1.])).tolist() == [0., .9999999999999999]
    draws = {(d['sequence'], d['commandlist_uid'], d['command_index']): d
             for d in json.loads((ROOT / 'Exports/CaptureBuffers/graphics_descriptor_bindings_probe.json').read_text())['dispatches']}
    recovery.TEXTURES = json.loads((OUT / 'texture_decode_manifest.json').read_text())
    specs = {
        'jacket': {'key': (25593, 2589, 473), 'pso': 31777, 'ps': 47612,
                   'cbv_uid': 5333, 'cbv_offset': 61392384,
                   'roughness_constant': None,
                   'color_stem': 'ellie-patrol-jacket-source-primary-color',
                   'normal_stem': 'ellie-patrol-jacket-source-primary-normal',
                   'ao_stem': 'ellie-patrol-jacket-ao',
                   'roughness_stem': 'ellie-patrol-jacket-source-primary-roughness'},
        'pants': {'key': (25593, 2589, 431), 'pso': 31807, 'ps': 47616,
                  'cbv_uid': 5331, 'cbv_offset': 299264,
                  'roughness_constant': .6700000166893005,
                  'color_stem': 'ellie-patrol-pants-source-primary-color',
                  'normal_stem': 'ellie-patrol-pants-normal',
                  'ao_stem': 'ellie-festival-pants-ao', 'roughness_stem': None}}
    rows = {}
    for name, spec in specs.items():
        draw = draws[spec['key']]
        assert draw['pipeline_uid'] == spec['pso']
        assert struct.unpack_from('<Q', object_blob(spec['pso'], 'create'), 767)[0] == spec['ps']
        view = draw['tables']['3']['slots'][2]
        cbv_source, raw = recovery.cbv_bytes(view, view['size'])
        assert cbv_source == {'resource_uid': spec['cbv_uid'], 'resource_offset': spec['cbv_offset']}
        raw_path = EVIDENCE / ('character_' + name + '_material_cbv.bin')
        raw_path.write_bytes(raw)
        regs = np.frombuffer(raw, '<f4').reshape(-1, 4)
        ids = [0, 1, 2, 7] if name == 'jacket' else [0, 1, 2, 4]
        textures = []
        for slot in ids:
            srv = draw['tables']['9']['slots'][slot]
            texture = recovery.original_texture(srv['resource_uid'])
            assert texture['original_texture_matches'], (name, slot, texture)
            textures.append({'shader_register': slot, 'srv_format': srv['format'],
                             'component_mapping': srv['mapping'], **texture})
        assert textures[0]['srv_format'] == 71
        global_source, global_raw = recovery.cbv_bytes(draw['tables']['3']['slots'][0], 3072)
        assert global_source == {'resource_uid': 7556, 'resource_offset': 100205312}
        assert struct.unpack_from('<f', global_raw, 66 * 16 + 8)[0] == 1
        tint = regs[0, :3].astype(np.float64)
        multiplier = 2. if name == 'jacket' else 2. * float(regs[0, 3])
        raw_rgb = png_array('ellie-patrol-' + name + '-color')
        encoded = np.clip(raw_rgb * tint * multiplier, 0, 1)
        linear = encoded ** 2.2
        derived = [save_png(spec['color_stem'], srgb_encode(linear), 'sRGB',
                            ['ellie-patrol-' + name + '-color'],
                            'standard_sRGB_encode(pow(saturate(raw_source_RGB*source_tint*source_multiplier),2.2))')]
        actual = png_array(spec['color_stem'])
        color_error = np.abs(srgb_decode(actual) - linear)
        source_normal_strength = 1.
        formulas = {'primary_encoded_color': '2*RawRGB*float3(.973,.91,.91)' if name == 'jacket' else '2*1.1*RawRGB*float3(1,.965,.906)',
                    'linear_color': 'pow(saturate(primary_encoded_color),2.2)',
                    'portable_color_png': 'standard_sRGB_encode(linear_color); texture sRGB=True',
                    'gbuffer_quantization': 'source saturates, Round_ne(encoded*255), packs uint RGB bytes; baked primary omits this intermediate quantization',
                    'roughness': 'lerp(.88,.5,saturate(1-jacket_metallic.R))' if name == 'jacket' else '.67',
                    'normal': 'existing original BC5 pants normal; no new scaling'}
        if name == 'jacket':
            source_normal_strength = float(regs[0, 3])
            normal_stem = Path(textures[1]['original_texture_matches'][0]['decoded_png']).stem
            assert normal_stem == 'ellie-patrol-jacket-normal_36950F2112783B58'
            normal = png_array(normal_stem)
            xy = (normal[:, :, :2] * 2 - 1) * source_normal_strength
            z = np.sqrt(np.clip(1 - np.sum(xy * xy, axis=2), 0, 1))
            vectors = np.concatenate([xy, z[:, :, None]], axis=2)
            # Source finally normalizes the tangent/world vector. This also
            # permits a normalized portable PNG if scaled XY lies outside the
            # unit disk; per-component clipping would change its direction.
            vectors /= np.maximum(np.linalg.norm(vectors, axis=2, keepdims=True), 1e-20)
            assert np.isfinite(vectors).all()
            derived.append(save_png(spec['normal_stem'], vectors * .5 + .5, 'Non-Color', [normal_stem],
                                    'xy=(BC5_RG*2-1)*1.3; z=sqrt(max(0,1-dot(xy,xy))); normalize(float3(xy,z)); encodeXYZ=normal*.5+.5; graphStrength=1'))
            metallic = png_array('ellie-patrol-jacket-metallic')[:, :, 0]
            mask = np.clip(1 - metallic, 0, 1)
            rough = float(regs[1, 0]) + (float(regs[5, 0]) - float(regs[1, 0])) * mask
            derived.append(save_png(spec['roughness_stem'], rough, 'Non-Color', ['ellie-patrol-jacket-metallic'], formulas['roughness']))
            formulas['normal'] = derived[-2]['equation']
        assert sha(OUT / ('ellie-patrol-' + name + '-color.png')) == next(r['png_sha256'] for r in recovery.TEXTURES if r['name'] == 'ellie-patrol-' + name + '-color.dds')
        png_sources = sorted({p for tex in textures for match in tex['original_texture_matches'] for p in [match['decoded_png']]})
        source = {'pipeline_uid': spec['pso'], 'pixel_shader_chunk': spec['ps'],
                  'draw_key': list(spec['key']), 'material_cbv': cbv_source,
                  'cbv_view_bytes': view['size'], 'raw_cbv': str(raw_path), 'raw_cbv_sha256': sha(raw_path),
                  'shader_reflected_logical_bytes': 276 if name == 'jacket' else 176,
                  'float4_registers': {str(i): v.tolist() for i, v in enumerate(regs[:15 if name == 'jacket' else 10])},
                  'global_cbv': global_source, 'global_reg66_z_color_multiplier': 1,
                  'final_material_color_multiplier_register': 'M14.z=1' if name == 'jacket' else 'M9.w=1',
                  'texture_bindings': textures,
                  'decoded_source_pngs': [{'path': p, 'png_sha256': sha(p)} for p in png_sources],
                  'source_ir': str(ROOT / 'Exports/CaptureBuffers/Shaders' / ('chunk_%d.asm.txt' % spec['ps'])),
                  'source_ir_sha256': sha(ROOT / 'Exports/CaptureBuffers/Shaders' / ('chunk_%d.asm.txt' % spec['ps'])),
                  'pipeline_create_blob_sha256': hashlib.sha256(object_blob(spec['pso'], 'create')).hexdigest()}
        rows[name] = {**{k: v for k, v in spec.items() if k.endswith('_stem') or k == 'roughness_constant'},
                      'ue_material_path': '/Game/TLOU2/Materials/Exact/M_ND_' + name,
                      'source_color_tint': tint.tolist(), 'source_encoded_color_multiplier': multiplier,
                      'source_normal_strength': source_normal_strength,
                      'portable_normal_node_strength': 1., 'formulas': formulas,
                      'source_evidence': source, 'derived_textures': derived,
                      'linear_color_quantized_png_error_max': float(color_error.max()),
                      'scope': 'Verified source primary approximation; original detail, wetness, mud, snow and other layers remain omitted.'}
    global_path = EVIDENCE / 'character_global_cbv.bin'
    global_path.write_bytes(global_raw)
    report = {'schema': 'source_character_material_manifest_v1', 'materials': rows,
              'source_global_cbv_raw': str(global_path), 'source_global_cbv_sha256': sha(global_path),
              'transfer_evidence': {'ir': str(ROOT / 'Exports/CaptureBuffers/Shaders/chunk_47284.asm.txt'),
                                    'ir_sha256': sha(ROOT / 'Exports/CaptureBuffers/Shaders/chunk_47284.asm.txt'),
                                    'lines': '311-332', 'source_exponent': 2.200000047683716,
                                    'encoded_clamp_pack': 'Jacket47612 lines2014-2016/2273-2275/2344-2363; pants47616 lines1421-1423/1719-1721/1790-1809. Saturate→Round_ne(*255)→uint bitpacking, not unconstrained float HDR.',
                                    'primary_ir': 'Jacket47612 lines592-619,654-655,1075-1077; pants47616 lines506-534,622-650.'},
              'limitations': ['These bakes reproduce source primary operations, not all source shader layers or original game lighting.',
                              'Additional source reflectance/cloth fields, including jacket M5.y*clothMask routed via SSA721 to1615, are not mapped to generic PBR channels. That field is not established as metalness; generic Metallic remains0.',
                              'The intermediate source8bit GBuffer quantization is omitted; portable PNGs themselves are8bit.',
                              'Source jacket M0.w=1.3 scales normalXY; it does not multiply color.',
                              'The existing DCC geometry uses reconstructed normals/tangents and flippedV UVs. Original captured tangent stream/handedness is not fully recovered. Normal XY/Z math is source-backed; complete original TBN/pixel orientation equivalence is not asserted. No unproven green-channel flip is added.',
                              'Jacket material shader reflection declares276B and actual view512B; numeric parameter registers0-14 are listed, with trailing packed metadata/padding retained only in the raw binary. Pants reflection176B/view256B; numeric parameters0-9 are listed.',
                              'Blender Principled has no AO input. Pants AO is retained as a glTF Occlusion node and for UE; it is not multiplied into base color.']}
    (ROOT / 'Exports/source_character_material_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (REPORT / 'CAPTURE_CHARACTER_SOURCE_PRIMARY_SHADER_PARAMS.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    md = ['# Captured character primary material evidence', '',
          'This report covers verified primary operations and exact source bindings. Original detail, wetness, mud, snow and game lighting remain outside this portable approximation.', '',
          '| Material | Source PS / CBV | Encoded primary RGB | Dry primary roughness |', '|---|---|---|---|',
          '| jacket | 47612 / UID5333 offset61392384 | `2*Raw*(.973,.91,.91)` | `lerp(.88,.5,saturate(1-metallic.R))` |',
          '| pants | 47616 / UID5331 offset299264 | `2*1.1*Raw*(1,.965,.906)` | `.67` |', '',
          'Source color views are BC1_UNORM. RGB is saturated and manually quantized to8bit before packing into integer GBuffer outputs. Deferred shader47284 lines311-332 unpacks bytes/255 and applies power2.2. The portable PNGs encode `pow(saturate(encodedPrimary),2.2)` with standard sRGB; import them with sRGB=True. Do not apply power2.2 a second time.', '',
          'Jacket source M0.w=1.3 scales signed BC5 normalXY before reconstructing positiveZ. The derived normal performs this operation and normalization, so its NormalMap node strength is1.0. The source t1/t3 UID33590 is the BC5 normal hash36950F2112783B58, distinct from the previously selected BC7 hash05DD7B5847C725B2.', '',
          'Original runtime tangent orientation is not fully recovered. Existing geometry retains its reconstructed normal/tangent basis and flippedV UVs; the source-backed XY/Z formula does not establish complete original TBN/pixel equivalence. No unproven green-channel flip is introduced.', '',
          'Pants source t2 UID33571 is byte-identical to the dictionary mip named `ellie-festival-pants-ao`. This is captured asset reuse, not an inferred outfit substitution.', '',
          'All CBV registers, raw binary paths, source and derived PNG hashes, captured mip hashes, dictionary offsets, and source IR locations are retained in the JSON report and `Exports/source_character_material_manifest.json`.']
    (REPORT / 'CAPTURE_CHARACTER_SOURCE_PRIMARY_SHADER_PARAMS.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'materials': list(rows), 'derived_textures': [d['stem'] for r in rows.values() for d in r['derived_textures']],
                      'transfer_png_error_max': {k: v['linear_color_quantized_png_error_max'] for k, v in rows.items()}}, indent=2))


if __name__ == '__main__':
    main()
