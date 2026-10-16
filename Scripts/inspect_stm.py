import os,glob,struct,collections
root=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97'
for p in [x for x in glob.glob(root+'\\*.stm') if os.path.getsize(x)<400000][:20]:
 b=open(p,'rb').read(); print('\n',os.path.basename(p),len(b));
 for sig in [b'ANIM',b'Oodle',b'ZSTD',b'\x78\x9c',b'\x78\xda',b'\x28\xb5\x2f\xfd',b'\x50\x4b\x03\x04',b'RAW',b'CLIP',b'BONE']:
  offs=[]; i=b.find(sig)
  while i>=0 and len(offs)<10: offs.append(i); i=b.find(sig,i+1)
  if offs: print(sig,offs)
 print('u32 first',struct.unpack('<32I',b[:128]))
