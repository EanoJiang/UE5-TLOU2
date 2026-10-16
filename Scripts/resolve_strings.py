import pefile
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;img=p.get_memory_mapped_image();md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
for va in [0x1418302da,0x14183035f,0x1418305b3,0x141830a68,0x141830a42]:
 rva=va-base
 for i in md.disasm(img[rva:rva+8],va):
  if i.mnemonic=='lea':
   op=i.operands[1];t=i.address+i.size+op.mem.disp;print(hex(va),i.op_str,'target',hex(t),'fileoff',hex(0x600+(t-base-0x1000))); f=0x600+(t-base-0x1000);print(img[t-base:t-base+100].split(b'\0')[0]);
