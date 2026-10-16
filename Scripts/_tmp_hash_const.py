import re
T={0x68fd26194ecb565a,0xc4bcadba8e631b86,0x52e7fc8056bc65d7}
def f(s):
 h=0xcbf29ce484222325
 for x in s.encode():h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
b=open(r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak','rb').read(); strs=[m.group().decode('ascii','ignore') for m in re.finditer(rb'[\x20-\x7e]{2,}',b)]
for s in set(strs):
 for x in [s,s+'\0',s.lower(),s.upper()]:
  if f(x) in T:print(hex(f(x)),repr(x))
# common all strings count
print('strings',len(strs))
