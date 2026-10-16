"""Pure-Python 0x060b unpack + 0x041b range decode, native-oracle checked.

The stream is read MSB first. The unpack leaf supplies a 64-bit sliding window
per destination lane; range decoding ignores bits below each lane's fields.
Range metadata stores quantized float32 scales/offsets and cross-lane predictors.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(r'D:/TLOU2_UE5_8_Codex')
EVIDENCE = ROOT / 'Exports/AnimationSources/DecodedRawChannels/codec_evidence'
MASK64 = (1 << 64) - 1


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def float_from_bits(bits):
    return struct.unpack('<f', struct.pack('<I', bits & 0xffffffff))[0]


def unpack_be_windows(stream: bytes, widths: list[int], initial_bit_offset: int = 0) -> list[int]:
    """Match leaf 0x218fa30's first u64 in each 16-byte output lane."""
    padded = stream + bytes(16)
    value = int.from_bytes(padded, 'big')
    size_bits = len(padded) * 8
    cursor = initial_bit_offset
    rows = []
    for width in widths:
        if not 0 <= width <= 128:
            raise ValueError(('unpack width', width))
        # Zero width leaves the owned scratch lane zero, as the native leaf does.
        rows.append((value >> (size_bits - cursor - 64)) & MASK64 if width else 0)
        cursor += width
    return rows


def parse_range_metadata(metadata: bytes, count: int) -> list[dict]:
    if len(metadata) < count * 20:
        raise ValueError('range metadata too short')
    rows = []
    for i in range(count):
        scale_word, offset_word = struct.unpack_from('<2Q', metadata, i * 16)
        width_word = struct.unpack_from('<I', metadata, count * 16 + i * 4)[0]
        bs = list(width_word.to_bytes(4, 'little'))
        scales = [
            float_from_bits((scale_word >> 33) & 0x7ffffe00),
            float_from_bits((scale_word >> 11) & 0x7ffffc00),
            float_from_bits((scale_word << 10) & 0x7ffffc00),
        ]
        offsets = [
            float_from_bits((offset_word >> 32) & 0xfffffc00),
            float_from_bits((offset_word >> 10) & 0xfffff800),
            float_from_bits((offset_word << 11) & 0xffffffff),
        ]
        rows.append({'track': i, 'raw_scale_u64': scale_word, 'raw_offset_u64': offset_word,
                     'raw_width_u32': width_word, 'scales_xyz': scales, 'offsets_xyz': offsets,
                     'widths_xyz': [bs[0] & 63, bs[1] & 63, bs[3] & 63],
                     'field_shifts': [0, bs[0] & 63, bs[2]],
                     'predictor_selectors_xyz': [bs[0] >> 6, bs[1] >> 6, bs[3] >> 6]})
    return rows


def range_decode_words(words: list[int], metadata: bytes | list[dict]) -> list[list[float]]:
    coeffs = parse_range_metadata(metadata, len(words)) if isinstance(metadata, bytes) else metadata
    if len(coeffs) != len(words):
        raise ValueError('range lane count mismatch')
    previous = [0.0, 0.0, 0.0, 0.0]
    output = []
    for word, coeff in zip(words, coeffs):
        quantized = []
        for width, shift in zip(coeff['widths_xyz'], coeff['field_shifts']):
            q = (((word << shift) & MASK64) >> (64-width)) if width else 0
            # The leaf converts signed dword integers to float32.
            q &= 0xffffffff
            quantized.append(q - (1 << 32) if q & (1 << 31) else q)
        vector = []
        for q, scale, offset, selector in zip(quantized, coeff['scales_xyz'], coeff['offsets_xyz'], coeff['predictor_selectors_xyz']):
            prediction = previous[selector-1] if selector else 0.0
            # Match separate SIMD mul/add operations, including float32 rounding.
            vector.append(f32(f32(f32(q) * scale) + f32(prediction + offset)))
        vector.append(0.0)
        previous = vector
        output.append(vector)
    return output


def decode_target_frames(codec: bytes) -> dict:
    widths = list(codec[0x210:0x214])
    coeffs = parse_range_metadata(codec[0x220:0x270], 4)
    frame_count = struct.unpack_from('<H', codec, 0x0e)[0]
    stride = struct.unpack_from('<H', codec, 0x3c)[0]
    start = struct.unpack_from('<I', codec, 0x38)[0]
    rows = []
    for frame in range(frame_count):
        data = codec[start + stride * frame:start + stride * (frame+1)]
        words = unpack_be_windows(data, widths)
        rows.append({'frame': frame, 'unpacked_u64': words, 'range_vectors': range_decode_words(words, coeffs)})
    return {'widths': widths, 'range_coefficients': coeffs, 'frame_count': frame_count, 'frame_stride': stride,
            'frame_stream_start': start, 'rows': rows}


def main():
    codec = (EVIDENCE/'ellie-prone-lg-aim-strafe-0-fw_41430102_payload.ndanim.bin').read_bytes()
    oracle_path = EVIDENCE/'native_leaf_range_oracle.json'
    oracle = json.loads(oracle_path.read_text(encoding='utf-8'))
    decoded = decode_target_frames(codec)
    unpack_matches, range_matches, max_error = 0, 0, 0.0
    for row, native in zip(decoded['rows'], oracle['rows']):
        unpack_match = row['unpacked_u64'] == native['native_unpacked_u64']
        range_match = row['range_vectors'] == native['range_vectors']
        unpack_matches += unpack_match
        range_matches += range_match
        max_error = max(max_error, max(abs(a-b) for pa, pb in zip(row['range_vectors'],native['range_vectors']) for a,b in zip(pa,pb)))
        row['native_unpack_exact_match'] = unpack_match
        row['native_range_exact_match'] = range_match
    result = {'tool': Path(__file__).name, 'target_clip': 'ellie-prone-lg-aim-strafe-0-fw',
              'oracle': str(oracle_path), 'native_unpack_leaf_rva':'0x218fa30',
              'native_range_leaf_rva':'0x21902d0', 'decoded':decoded,
              'verification':{'frames':80,'unpack_bit_exact_matches':unpack_matches,
                              'range_float32_exact_matches':range_matches,'compared_xyz_scalars':80*4*3,
                              'max_absolute_error':max_error},
              'pass':unpack_matches==range_matches==80 and max_error==0.0,
              'scope':'Unpack and range decode only. Quaternion log/PCA postprocessing is a separate established leaf.'}
    path = ROOT/'Content/TLOU2/Reports/DYNAMIC_UNPACK_RANGE_PYTHON_VERIFICATION.json'
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    (EVIDENCE/'python_dynamic_range_frames.json').write_text(json.dumps(decoded,indent=2),encoding='utf-8')
    md = ['# Pure-Python dynamic unpack and range verification','',
          'The 0x060b 128-bit-lane unpack and 0x041b range decoder now reproduce the isolated original executable leaves across all target frames.', '',
          '- Correct unpack leaf: RVA `0x218fa30` (16-byte output lanes). The nearby `0x218fbe0` writes 32-bit scalar lanes and is unsuitable for the 33/34-bit vector tracks.',
          '- MSB-first sliding-window positions: 0,33,67,101 bits within each 15-byte frame; widths33,34,34,12.',
          '- Range metadata reconstructs float32 scales and offsets from two packed u64 words per track.',
          '- Each component width byte includes a two-bit predictor selector. Selectors1..3 add X/Y/Z from the previous decoded track; zero means no predictor.',
          '- Float32 multiplication and both additions are rounded separately, matching the SIMD instructions.', '',
          f'- Bit-exact unpack frames: **{unpack_matches}/80**.',
          f'- Float32-exact range frames: **{range_matches}/80**, comparing960 XYZ scalars.',
          f'- Maximum absolute error: **{max_error}**.', '',
          'The Python module exposes `unpack_be_windows`, `parse_range_metadata`, `range_decode_words`, and `decode_target_frames` for the final source animation decoder.']
    path.with_suffix('.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(path),'verification':result['verification'],'pass':result['pass']},indent=2))
    if not result['pass']:raise SystemExit(1)


if __name__=='__main__':main()
