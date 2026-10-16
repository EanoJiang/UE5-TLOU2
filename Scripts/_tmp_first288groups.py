import struct,json,collections
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();page=9541328;rel=0x8e150;raw=b[page+rel:page+rel+0x30000];joint=0x52e7fc8056bc65d7;D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={f(x['name']):x['name'] for x in D['bones']};m=[]
for o in range(len(raw)-16):
 if struct.unpack_from('<Q',raw,o)[0]==joint and struct.unpack_from('<Q',raw,o+8)[0] in by:m.append(o)
first=m[:288]; runs=[];cur=[]
for o in first:
 if not cur or o-cur[-1]==48:cur.append(o)
 else:runs.append(cur);cur=[o]
runs.append(cur)
print('runs',len(runs),[(hex(r[0]),hex(r[-1]),len(r),hex(rel+r[0]),hex(rel+r[-1])) for r in runs]);
for i,r in enumerate(runs):print(i,len(r),collections.Counter(by[struct.unpack_from('<Q',raw,o+8)[0]] for o in r))
