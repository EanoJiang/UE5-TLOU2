import pefile,sys
from capstone import *
f='D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe';pe=pefile.PE(f);print('base',hex(pe.OPTIONAL_HEADER.ImageBase));
for s in pe.sections: print(s.Name,s.PointerToRawData,s.SizeOfRawData,hex(s.VirtualAddress),hex(s.Misc_VirtualSize))
o=0x182f90f; sec=next(s for s in pe.sections if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData);rva=sec.VirtualAddress+(o-sec.PointerToRawData);va=pe.OPTIONAL_HEADER.ImageBase+rva; print('magic file',hex(o),'rva',hex(rva),'va',hex(va),'sec',sec.Name)
code=pe.get_memory_mapped_image()[rva-128:rva+512];md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
for i in md.disasm(code,va-128): print(hex(i.address),i.mnemonic,i.op_str)
