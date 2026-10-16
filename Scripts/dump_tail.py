import glob,struct,os
p=glob.glob(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\\*chunk0000\\source.pak')[0]; b=open(p,'rb').read();
for off in [0x18b0,0x18d0,0x1900,0x1940,0x1980,0x19c0]:
 print('\n',hex(off)); print(' '.join(f'{x:02x}' for x in b[off:off+128]));
