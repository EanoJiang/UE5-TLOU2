import json,itertools
T={0x05fed8d7a1d8cf89,0x0b5689834f4c5a68,0x0b568b834f4c5dce,0x0b568c834f4c5f81,0x0b568d834f4c6134,0x0b568e834f4c62e7,0x0b568f834f4c649a,0x0b5690834f4c664d,0x0ea32384d9780bd8,0x0ea32484d9780d8b,0x0ea32584d9780f3e,0x0ea32784d97812a4,0x0ea32884d9781457,0x0ea32984d978160a,0x0ea32a84d97817bd,0x4f02cf97446f2088,0x4f02d097446f223b,0x4f02d297446f25a1,0x4f02d397446f2754,0x4f02d497446f2907,0x4f02d597446f2aba,0x4f02d697446f2c6d,0x36e4b80543fcd944,0x36e4be0543fce376,0x2aa13a7f2c790fd1,0x2aa1447f2c7920cf,0xb0599017cc83e626,0x16ae0a786c0a62e0,0xf2099db117ba20bc,0x5a52202ce3f64436,0x509903bb65ac341e}
def f(d):
 h=0xcbf29ce484222325
 for x in d:h=((h^x)*0x100000001b3)&0xffffffffffffffff
 return h
D=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\ExactDebug\ellie16_patrol_body\capture.json')); names=[x['name'] for x in D['bones']]
seps=['','_','.','/','|',':','-',' ']; toks=['x','y','z','q','quat','rotation','translation','position','scale','rot','trans','pos','root','channel','0','1','2','3','4','5','6','7','8','9']
post=['','\0']+[f'_{i}' for i in range(100)]+[f'.{i}' for i in range(100)]+[f'|{i}' for i in range(100)]
h={}
for n in names:
 for a in [n,n.lower(),n.upper()]:
  for x in [a]+[a+s+t for s in seps for t in toks]+[a+t+s for s in seps for t in toks]+[a+s for s in post]:
   for y in [x,x+'\0']:
    q=f(y.encode())
    if q in T:h.setdefault(q,[]).append(y)
print('hits',len(h)); [print(hex(k),v[:10]) for k,v in h.items()]
