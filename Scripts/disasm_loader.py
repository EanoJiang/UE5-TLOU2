import pefile
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase
# map VA to RVA
va=0x141442d60;rva=va-base;c=p.get_memory_mapped_image()[rva-0x100:rva+0x600];md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True
for i in md.disasm(c,va-0x100):print(hex(i.address),i.mnemonic,i.op_str)
