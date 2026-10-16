import zlib
p=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'; b=open(p,'rb').read()
for off in [11026,20197]:
 for wb in range(-15,32):
  try:
   d=zlib.decompressobj(wb).decompress(b[off:]); print(off,wb,len(d));break
  except Exception as e:
   if wb in [15,-15,31]: print(off,wb,repr(e))
