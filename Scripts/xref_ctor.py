import pefile
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');o=0x14423e9;rva=0x1000+(o-0x600);va=p.OPTIONAL_HEADER.ImageBase+rva;c=p.get_memory_mapped_image()[rva-300:rva+300];md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True
for i in md.disasm(c,va-300):print(hex(i.address),i.mnemonic,i.op_str)
