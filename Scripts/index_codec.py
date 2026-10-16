import struct
samples=['020143414c1bbe5ae0230000070029000000000030000000d02300000000f04100002900cdcccc3c000020428988083d2001000000007f00400f00004d00b000']
for s in samples:
 b=bytes.fromhex(s)
 for o in range(0,len(b),4): print(o,b[o:o+4].hex(), struct.unpack_from('<I',b,o)[0],struct.unpack_from('<f',b,o)[0])
