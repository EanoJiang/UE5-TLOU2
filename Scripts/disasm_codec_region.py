import pefile
from capstone import *
f='D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe';pe=pefile.PE(f);o=0x182f90f;sec=next(s for s in pe.sections if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData);rva=sec.VirtualAddress+(o-sec.PointerToRawData);va=pe.OPTIONAL_HEADER.ImageBase+rva;img=pe.get_memory_mapped_image();code=img[rva-0x100:rva+0x5000];md=Cs(CS_ARCH_X86,CS_MODE_64);md.skipdata=True
for i in md.disasm(code,va-0x100):
 if i.mnemonic in ('mov','movzx','movsx','lea','cmp','test','and','or','shl','shr','sar','imul','add','sub','call','jmp','ret') and (0x1418302c0<=i.address<=0x141834000): print(hex(i.address),i.mnemonic,i.op_str)
