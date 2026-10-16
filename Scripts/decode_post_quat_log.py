"""Portable OrbisAnim PostQuatLog, verified against the executable math leaf.

Input is the decompressed float4 scratch stream and packed pairwise snorm16
base quaternions. Values intentionally retain game polynomial and quantization
error: no normalization, smoothing, synthetic motion, or fit is applied.
"""
import json,math,struct
from pathlib import Path

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
EVIDENCE=ROOT/'Exports/AnimationSources/DecodedRawChannels/codec_evidence'

def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]

def mul(a,b):return f32(a*b)
def fma(a,b,c):return f32(a*b+c)

# Exact float32 constants read through RIP references in RVA 0x2196d70.
S0=-0.00018759677186608315
S1=0.008323054760694504
S2=-0.1666666716337204
C0=-0.001292107393965125
C1=0.04157479852437973
SNORM_SCALE=3.0517578125e-05

def unpack_base_quaternions(packed,count):
    result=[]
    for pair in range((count+1)//2):
        shorts=struct.unpack_from('<8h',packed,pair*16)
        for parity in range(2):
            result.append([mul(shorts[2*i+parity],SNORM_SCALE) for i in range(4)])
    return result[:count]

def post_quat_log(vector,base):
    x,y,z=map(f32,vector[:3])
    # Instruction order is y*y; FMA(x*x); FMA(z*z).
    square=fma(z,z,fma(x,x,mul(y,y)))
    sinc=fma(square,fma(square,fma(square,S0,S1),S2),1.0)
    cosine=fma(square,fma(square,fma(square,C0,C1),-0.5),1.0)
    ex,ey,ez=mul(x,sinc),mul(y,sinc),mul(z,sinc)
    bx,by,bz,bw=base
    # base * exp(log), in executable FMA instruction order.
    ox=fma(-bz,ey,fma(ex,bw,fma(ez,by,mul(cosine,bx))))
    oy=fma(-bx,ez,fma(ey,bw,fma(bz,ex,mul(cosine,by))))
    oz=fma(-by,ex,fma(ez,bw,fma(ey,bx,mul(cosine,bz))))
    ow=fma(-bz,ez,fma(-by,ey,fma(bw,cosine,-mul(bx,ex))))
    return [ox,oy,oz,ow]

def main():
    oracle_path=EVIDENCE/'native_leaf_range_oracle.json'
    oracle=json.loads(oracle_path.read_text(encoding='utf-8'))
    blob=(EVIDENCE/'ellie-prone-lg-aim-strafe-0-fw_41430102_payload.ndanim.bin').read_bytes()
    bases=unpack_base_quaternions(blob[0x270:0x290],4)
    rows=[];max_error=0.0;count_exact=0;max_angular_error=0.0
    for row in oracle['rows']:
        out=[]
        for vector,base,native in zip(row['range_vectors'],bases,row['quaternions_xyzw']):
            quaternion=post_quat_log(vector,base)
            error=max(abs(a-b) for a,b in zip(quaternion,native))
            exact=struct.pack('<4f',*quaternion)==struct.pack('<4f',*native)
            count_exact+=int(exact)
            max_error=max(max_error,error)
            n0=math.sqrt(sum(v*v for v in quaternion));n1=math.sqrt(sum(v*v for v in native))
            dot=min(1.0,abs(sum(a*b for a,b in zip(quaternion,native))/(n0*n1)))
            max_angular_error=max(max_angular_error,0.0 if exact else math.degrees(2*math.acos(dot)))
            out.append(quaternion)
        rows.append({'frame':row['frame'],'quaternions_xyzw':out})
    report={'status':'PASS' if max_error<2e-7 else 'FAIL','frames':len(rows),'tracks':4,'quaternions_compared':len(rows)*4,'float4_bit_exact':count_exact,'max_component_error':max_error,'max_angular_error_degrees':max_angular_error,'snorm_scale':SNORM_SCALE,'base_quaternions_xyzw':bases,'executable_leaf_rva':'0x2196d70','polynomial_sinc':[1.0,S2,S1,S0],'polynomial_cos':[1.0,-0.5,C1,C0],'order':'base quaternion Hamilton multiplied by exp(log vector)','limitation':'This verifies PostQuatLog on independently native-decoded Range inputs. Full codec verification also requires bit-unpack, range, section, bone mapping, and destination scatter validation.'}
    (EVIDENCE/'portable_post_quat_log.json').write_text(json.dumps({'validation':report,'rows':rows},indent=2),encoding='utf-8')
    (ROOT/'Content/TLOU2/Reports/POST_QUAT_LOG_PORTABLE_VALIDATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if report['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
