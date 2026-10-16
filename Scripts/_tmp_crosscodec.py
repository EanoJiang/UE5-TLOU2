import struct,glob,os
T=[0x52e7fc8056bc65d7,0x2950bb040960d515,0xfb5972f31b48cb0f,0x9235c0b22295b632,0x98b1c9c760c09e6c,0xb35089339429a0b0,0x83017c71debf63b,0xfb5974f31b48ce75,0x1932141f23d602f1]
for p in glob.glob(r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-*.pak'):
 b=open(p,'rb').read(); hits=[]
 for x in T:
  q=b.find(struct.pack('<Q',x)); hits.append(q)
 if hits[0]>=0:
  # check immediate sequence around first joint hash
  q=hits[0]; seq=[]
  for j in range(8):
   o=q+48*j; seq.append(struct.unpack_from('<Q',b,o+8)[0] if o+16<=len(b) else None)
  print(os.path.basename(p),q, [hex(x) if x is not None else None for x in seq])
