import struct,collections,json
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();po=9541328; rel=0xac3b0; raw=b[po+rel:po+rel+0x30000]; joint=0x52e7fc8056bc65d7
for name,x in [('A',raw)]:
 starts=[]
 for o in range(0,len(x)-8):
  if struct.unpack_from('<Q',x,o)[0]==joint: starts.append(o)
 print(name,'joint markers',len(starts),starts[:100]);print('deltas',collections.Counter(starts[i+1]-starts[i] for i in range(len(starts)-1)).most_common(20))
 # for each marker, bone candidate qword at marker+8
 D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'))
 def f(s):
  h=0xcbf29ce484222325
  for y in s.encode():h=((h^y)*0x100000001b3)&0xffffffffffffffff
  return h
 by={f(z['name']):z['name'] for z in D['bones']}
 for o in starts[:100]:
  vals=[struct.unpack_from('<Q',x,o+i)[0] if o+i+8<=len(x) else None for i in [-8,0,8,16,24]]
  print(o, [hex(v) if v is not None else None for v in vals], 'bone_at+8',by.get(vals[2]),'bone_at+16',by.get(vals[3]))
