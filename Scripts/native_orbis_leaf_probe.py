"""Isolated native oracle for a bounded, no-external-call OrbisAnim leaf.

Loads a copy of executable sections into this child Python process without
running its entry point, TLS callbacks, constructors, or game code. Only a
specified math leaf is called, with small owned input/output arrays.
"""
import ctypes as C
import json
import math
import struct
from pathlib import Path
import pefile

ROOT = Path(r"D:/TLOU2_UE5_8_Codex")
EXE = Path(r"D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe")


def load_image():
    pe = pefile.PE(str(EXE), fast_load=True)
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.VirtualAlloc.argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_uint32]
    kernel.VirtualAlloc.restype = C.c_void_p
    requested = pe.OPTIONAL_HEADER.ImageBase
    base = kernel.VirtualAlloc(requested, pe.OPTIONAL_HEADER.SizeOfImage, 0x3000, 0x40)
    if base != requested:
        raise RuntimeError(f"preferred image allocation failed: {base!r}, {C.get_last_error()}")
    C.memmove(base, bytes(pe.__data__[:pe.OPTIONAL_HEADER.SizeOfHeaders]), pe.OPTIONAL_HEADER.SizeOfHeaders)
    for section in pe.sections:
        data = section.get_data()
        if data:
            C.memmove(base + section.VirtualAddress, data, len(data))
    # Const quaternion SIMD leaf indexes a runtime-generated swap permutation.
    permutations = [[3, 1, 2, 0], [0, 3, 2, 1], [0, 1, 3, 2], [0, 1, 2, 3]]
    C.memmove(base + 0x95E82B0, b"".join(struct.pack("<4I", *p) for p in permutations), 64)
    return base


def main():
    base = load_image()
    codec = (ROOT / "Exports/AnimationSources/DecodedRawChannels/codec_evidence/ellie-prone-lg-aim-strafe-0-fw_41430102_payload.ndanim.bin").read_bytes()
    # Independently decoded constant q48 input is a guard before dynamic math.
    native_const = C.WINFUNCTYPE(None, C.c_uint16, C.c_void_p, C.c_void_p, C.c_void_p)(base + 0x218F050)
    data = C.create_string_buffer(codec[0x1F0:0x1F0+48], 64)
    table = C.create_string_buffer(struct.pack("<8H", *[16*i for i in range(8)]))
    output = C.create_string_buffer(128)
    native_const(8, C.addressof(output), C.addressof(data), C.addressof(table))
    const_quats = [list(struct.unpack_from("<4f", output.raw, 16*i)) for i in range(3)]
    if max(abs(a-b) for a,b in zip(const_quats[1], [0,0,0,1])) > 1e-6:
        raise RuntimeError("native constant quaternion guard failed")
    # Decompress3VecRange in-place leaf: uint16 count, scratch, stride, metadata.
    native_range = C.WINFUNCTYPE(None, C.c_uint16, C.c_void_p, C.c_size_t, C.c_void_p)(base + 0x21902D0)
    native_unpack = C.WINFUNCTYPE(None, C.c_uint16, C.c_void_p, C.c_void_p, C.c_size_t, C.c_void_p, C.c_void_p, C.c_void_p)(base + 0x218FA30)
    native_postlog = C.WINFUNCTYPE(None, C.c_uint16, C.c_void_p, C.c_size_t, C.c_void_p)(base + 0x2196D70)
    metadata = C.create_string_buffer(codec[0x220:0x270])
    widths = C.create_string_buffer(codec[0x210:0x220])
    post_metadata = C.create_string_buffer(codec[0x270:0x290])
    rows=[]
    for frame in range(80):
        frame_bytes=codec[0x500+15*frame:0x500+15*(frame+1)]
        bits=int.from_bytes(frame_bytes,"big")
        scratch=C.create_string_buffer(64)
        cursor=0
        quant=[]
        for i,width in enumerate(codec[0x210:0x214]):
            val=(bits>>(120-cursor-width))&((1<<width)-1)
            quant.append(val)
            struct.pack_into("<Q",scratch,i*16,val<<(64-width))
            cursor+=width
        manual=C.create_string_buffer(scratch.raw,64)
        native_range(0x8004,C.addressof(manual),16,C.addressof(metadata))
        C.memset(C.addressof(scratch),0,64)
        stream=C.create_string_buffer(frame_bytes,48)
        native_unpack(0x8004,C.addressof(scratch),0,16,C.addressof(stream),C.addressof(stream),C.addressof(widths))
        unpacked=[struct.unpack_from("<Q",scratch.raw,16*i)[0] for i in range(4)]
        native_range(0x8004,C.addressof(scratch),16,C.addressof(metadata))
        range_vectors=[list(struct.unpack_from("<4f",scratch.raw,16*i)) for i in range(4)]
        unpack_equal=scratch.raw==manual.raw
        native_postlog(4,C.addressof(scratch),16,C.addressof(post_metadata))
        quats=[list(struct.unpack_from("<4f",scratch.raw,16*i)) for i in range(4)]
        rows.append({"frame":frame,"quant":quant,"native_unpacked_u64":unpacked,"range_vectors":range_vectors,"manual_unpack_range_equal":unpack_equal,"quaternions_xyzw":quats,"quaternion_norms":[math.sqrt(sum(c*c for c in q)) for q in quats]})
    out={"native_const_quats":const_quats,"leaf_range_rva":"0x21902d0","rows":rows}
    path=ROOT/"Exports/AnimationSources/DecodedRawChannels/codec_evidence/native_leaf_range_oracle.json"
    path.write_text(json.dumps(out,indent=2))
    print(json.dumps({"constant_guard":const_quats,"first":rows[0],"last":rows[-1],"output":str(path)},indent=2))


if __name__ == "__main__":
    main()
