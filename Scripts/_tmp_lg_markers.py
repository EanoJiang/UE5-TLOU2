import struct,collections,json
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();po=9541328;rel=0x8e150;raw=b[po+rel:po+rel+0x30000];joint=0x52e7fc8056bc65d7;starts=[o for o in range(len(raw)-8) if struct.unpack_from('<Q',raw,o)[0]==joint];print('count',len(starts));print('first',starts[:100]);print('delta',collections.Counter(starts[i+1]-starts[i] for i in range(len(starts)-1)).most_common(20));
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={f(x['name']):x for x in D['bones']}
# print contiguous runs with 48 stride
runs=[];cur=[starts[0]]
for a,b2 in zip(starts,starts[1:]):
 if b2-a==48:cur.append(b2)
 else:runs.append(cur);cur=[b2]
runs.append(cur)
for run in runs[:30]:
 print('RUN',run[0],run[-1],'n',len(run),'delta',run[-1]-run[0]);
 print([by.get(struct.unpack_from('<Q',raw,o+8)[0],{}).get('name') for o in run[:40]])
