import pathlib,math,struct,json,numpy as np
b=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak').read_bytes();q=0x95ae20;stream=b[q+0x500:q+0x9b0];N=80
# decode 48bit q at bit offset relative each frame
# signed15, tag3; omitted bits low2, sign bit2
sc=math.sqrt(.5)/16384

def qdec(w):
 tag=(w>>45)&7; vals=[]
 for i in range(3):
  z=(w>>(15*i))&0x7fff
  if z&0x4000:z-=0x8000
  vals.append(z*sc)
 omit=tag&3; sign=-1 if (tag&4) else 1; s=1-sum(x*x for x in vals); om=math.sqrt(max(0,s))*sign if s>=0 else float('nan'); o=[];j=0
 for i in range(4):
  o.append(om if i==omit else vals[j]);j+=i!=omit
 return o

def getbits(dat,bit,n):
 x=int.from_bytes(dat,'little'); return (x>>bit)&((1<<n)-1)
for off in range(0,121):
 qs=[]; bad=0
 for f in range(N):
  d=stream[f*15:(f+1)*15];w=getbits(d,off,48);v=qdec(w);bad+=sum(math.isnan(x) for x in v);qs.append(v)
 # sign-invariant angular step between consecutive q
 smooth=[]
 for a,z in zip(qs,qs[1:]):
  dot=abs(sum(x*y for x,y in zip(a,z)));smooth.append(dot)
 score=sum(smooth)/len(smooth)
 if score>.95 and bad==0:print(off,'score',score,'min',min(smooth),'first',qs[0])
