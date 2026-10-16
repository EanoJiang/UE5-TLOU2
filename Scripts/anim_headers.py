import struct,glob,os
for p in glob.glob(r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\\*.stm'):
 b=open(p,'rb').read(); poss=[]; i=0
 while 1:
  i=b.find(b'ANIMMAGICSTR',i)
  if i<0: break
  poss.append(i-4);i+=1
 if not poss: continue
 s=poss[0]; e=poss[1] if len(poss)>1 else len(b); cb=b[s+16:e+16];
 try:
  po=struct.unpack_from('<3I',cb,44)[0]; ro=struct.unpack_from('<QI',cb,po+20)[1]; rs=po+ro
  vals=struct.unpack_from('<16I',cb,rs+48)
  print(os.path.basename(p), 'len',len(b),'chunk',e-s,'rs',rs,'vals',' '.join(hex(v) for v in vals))
 except: pass
