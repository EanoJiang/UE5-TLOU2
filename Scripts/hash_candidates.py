import struct, hashlib
targets=[0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e]
names=['ANIM_RAWCHANNELS','ANIM','ANIM_GROUP','bindpose-add','bindpose-anim','root','pelvis','spinea','spineb','spinec','neck','heada','headb','rotation','translation','scale','quat','position','raw','channels']
def fnv1a(data):
 h=0xcbf29ce484222325
 for c in data:
  h^=c; h=(h*0x100000001b3)&0xffffffffffffffff
 return h
def fnv1(data):
 h=0xcbf29ce484222325
 for c in data:
  h=(h*0x100000001b3)&0xffffffffffffffff; h^=c
 return h
for s in names:
 d=s.encode(); print(s, hex(fnv1a(d)),hex(fnv1(d)),hashlib.sha1(d).hexdigest()[:16])
print('targets',[hex(x) for x in targets])
