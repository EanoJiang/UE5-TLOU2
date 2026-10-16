import json,struct,collections,os
PAK=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak'; CAP=r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json'; # target codec from report
D=json.load(open(CAP));
def fnv(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
by={fnv(x['name']):x for x in D['bones']}
# target payload from report
rpt=json.load(open(r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\Reports\CODEC_41430102_STRUCTURE_TARGET.json')); a=rpt['codec_absolute_offset']; n=rpt['header']['payload_size']; b=open(PAK,'rb').read()[a:a+n];print('payload',a,n,len(b))
hits=[]
for o in range(0,len(b)-8):
 x=struct.unpack_from('<Q',b,o)[0]
 if x in by: hits.append((o,x,by[x]))
print('hash hits',len(hits),'unique',len({x for _,x,_ in hits}));
for x in hits:print(x)
# all aligned 8 only
print('aligned hits',[(o,hex(x),by[x]['name']) for o in range(0,len(b)-8,8) if (x:=struct.unpack_from('<Q',b,o)[0]) in by][:100])
# derive all FNV hash from ascii strings? 
