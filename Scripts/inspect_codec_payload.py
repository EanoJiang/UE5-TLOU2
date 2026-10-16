import struct,sys,os
p=sys.argv[1]; b=open(p,'rb').read()
print('FILE',p,'len',len(b))
for base in [0]:
 print('HEADER')
 for o in range(0,96,4):
  print(f'{o:02x}: u32={struct.unpack_from("<I",b,o)[0]:08x} u16={struct.unpack_from("<H",b,o)[0]:04x},{struct.unpack_from("<H",b,o+2)[0]:04x} f32={struct.unpack_from("<f",b,o)[0]:.8g}')
 print('BYTES',b[:128].hex(' '))
 for off in [0x40,0x50,0x60,0x80,0x100,0x200,0x400,0x550,0x560,0x580]:
  if off>=len(b): continue
  print('BLOCK',hex(off),b[off:off+128].hex(' '))
  print('HALF', [round(struct.unpack_from('<e',b,off+i)[0],6) for i in range(0,min(128,len(b)-off-1),2)])
