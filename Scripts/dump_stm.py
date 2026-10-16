import struct,glob,os
p=glob.glob(r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\\*.stm')[10]
b=open(p,'rb').read(); print(os.path.basename(p),len(b))
for sig in [b'ANIM',b'RAW']:
 print('\n',sig)
 i=0
 while 1:
  i=b.find(sig,i)
  if i<0:break
  print('off',i,'hex',b[i:i+160].hex(' ')); i+=1
