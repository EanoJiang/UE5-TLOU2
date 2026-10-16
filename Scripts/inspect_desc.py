import struct,glob
p=glob.glob(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\\*chunk0000\\source.pak')[0];b=open(p,'rb').read();p0=0x100; start=p0+52; print('start',hex(start));
for i in range(24):
 d=b[start+i*12:start+(i+1)*12]; print(i,d.hex(' '),'u16',struct.unpack('<6H',d),'u32',struct.unpack('<3I',d))
