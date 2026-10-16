import pefile
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;img=p.get_memory_mapped_image();
for fo in [0x3032a60,0x3032c50,0x2ec3944,0x2b036f0,0x25f8087]:
 sec=next(s for s in p.sections if s.PointerToRawData<=fo<s.PointerToRawData+s.SizeOfRawData);rva=sec.VirtualAddress+fo-sec.PointerToRawData;va=base+rva;c=img[rva-0x100:rva+0x400];md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True;print('\n===',hex(fo),hex(va))
 for i in md.disasm(c,va-0x100):print(hex(i.address),i.mnemonic,i.op_str)
