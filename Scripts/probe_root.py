import struct,json,os
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read(); pageoff=121376; rs=1157136; count=struct.unpack_from('<I',b,rs+48)[0]; hptr=struct.unpack_from('<Q',b,rs+56)[0]; dptr=struct.unpack_from('<Q',b,rs+64)[0]; print(count,hex(hptr),hex(dptr),hex(pageoff+hptr),hex(pageoff+dptr)); hashes=[struct.unpack_from('<Q',b,pageoff+hptr+i*8)[0] for i in range(count)]; descs=[struct.unpack_from('<Q',b,pageoff+dptr+i*8)[0] for i in range(count)];
for i,(h,d) in enumerate(zip(hashes,descs)):
 o=pageoff+d; fmt=struct.unpack_from('<I',b,o)[0]; dp=struct.unpack_from('<Q',b,o+8)[0] if o+16<=len(b) else 0
 print(i,hex(h), 'desc_rel',hex(d),'abs',o,'fmt',hex(fmt),'dp',hex(dp),'dataabs',pageoff+dp, 'head',b[o:o+32].hex(' '))
 if h==0x509903bb65ac341e: print('ROOT_INDEX',i)
