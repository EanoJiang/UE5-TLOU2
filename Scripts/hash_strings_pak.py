import struct,re,sys,os
p=sys.argv[1] if len(sys.argv)>1 else r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak'
b=open(p,'rb').read()
targets=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
def fnv(s):
 h=0xcbf29ce484222325
 for c in s: h=((h^c)*0x100000001b3)&0xffffffffffffffff
 return h
hits={t:[] for t in targets}
for m in re.finditer(rb'[\x20-\x7e]{3,80}\0',b):
 s=m.group()[:-1].decode('utf8','replace'); h=fnv(s.encode())
 if h in hits: hits[h].append((s,m.start()))
print(hits)
