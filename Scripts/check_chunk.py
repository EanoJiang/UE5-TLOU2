import pathlib,struct,glob
p=glob.glob(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\\*.chunk0000\\source.pak')[0]; b=open(p,'rb').read(); print(p,len(b)); print('magic offs', [i for i in range(len(b)) if b.startswith(b'\x02\x01CA',i)][:20]);
for o in [0x100,0x104,0x108,0x10c,0x110,0x114,0x118,0x11c,0x120,0x124,0x128,0x12c,0x130]: print(hex(o),b[o:o+8].hex(' '))
