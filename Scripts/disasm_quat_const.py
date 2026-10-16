import pefile
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;fo=0x25f8087;sec=next(s for s in p.sections if s.PointerToRawData<=fo<s.PointerToRawData+s.SizeOfRawData);rva=sec.VirtualAddress+fo-sec.PointerToRawData;va=base+rva;img=p.get_memory_mapped_image();c=img[rva-0x200:rva+0x900];md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True
for i in md.disasm(c,va-0x200):print(hex(i.address),i.mnemonic,i.op_str)
