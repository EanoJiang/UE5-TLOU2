"""Independent native oracle for the 128-bit-lane unpack leaf 0x218fa30."""
import ctypes as C
import json
import struct
from pathlib import Path
from native_orbis_leaf_probe import load_image, ROOT


def main():
    base=load_image()
    codec=(ROOT/'Exports/AnimationSources/DecodedRawChannels/codec_evidence/ellie-prone-lg-aim-strafe-0-fw_41430102_payload.ndanim.bin').read_bytes()
    unpack=C.WINFUNCTYPE(None,C.c_uint16,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p)(base+0x218FA30)
    range_decode=C.WINFUNCTYPE(None,C.c_uint16,C.c_void_p,C.c_size_t,C.c_void_p)(base+0x21902D0)
    widths=C.create_string_buffer(codec[0x210:0x220])
    metadata=C.create_string_buffer(codec[0x220:0x270])
    rows=[]
    for frame in range(80):
        data=codec[0x500+15*frame:0x500+15*(frame+1)]
        stream=C.create_string_buffer(data,48)
        output=C.create_string_buffer(64)
        unpack(0x8004,C.addressof(output),0,16,C.addressof(stream),C.addressof(stream),C.addressof(widths))
        unpacked=[struct.unpack_from('<Q',output.raw,16*i)[0] for i in range(4)]
        range_decode(0x8004,C.addressof(output),16,C.addressof(metadata))
        rows.append({'frame':frame,'unpacked_u64':unpacked,'range_vectors':[list(struct.unpack_from('<4f',output.raw,16*i)) for i in range(4)]})
    out={'leaf_unpack_rva':'0x218fa30','leaf_range_rva':'0x21902d0','frame_count':80,'rows':rows}
    path=ROOT/'Exports/AnimationSources/DecodedRawChannels/codec_evidence/native_unpack128_range_oracle.json'
    path.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({'path':str(path),'first':rows[0],'last':rows[-1]},indent=2))


if __name__=='__main__':main()
