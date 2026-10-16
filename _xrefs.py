import pefile, pathlib, struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
p=pathlib.Path(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');pe=pefile.PE(str(p)); b=p.read_bytes();
for needle in [b'OrbisAnim::ConstDecompressQuat48SmallestThree',b'OrbisAnim::DecompressQuatSmallestThree',b'ConstDecompress3VecFloat16',b'Decompress3VecRange',b'PostDecompressQuatLog',b'PostDecompressQuatLogPca']:
 off=b.find(needle);print(needle,hex(off), 'rva',hex(pe.get_rva_from_offset(off)) if off>=0 else None)
# map every executable section and search RIP refs to string address
md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
for needle in [b'OrbisAnim::ConstDecompressQuat48SmallestThree',b'OrbisAnim::DecompressQuatSmallestThree',b'ConstDecompress3VecFloat16',b'Decompress3VecRange',b'PostDecompressQuatLog',b'PostDecompressQuatLogPca']:
 off=b.find(needle);target=pe.OPTIONAL_HEADER.ImageBase+pe.get_rva_from_offset(off)
 print('\nSTR',needle,target)
 for sec in pe.sections:
  if not sec.IMAGE_SCN_MEM_EXECUTE:continue
  sb=sec.get_data(); va=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress
  for ins in md.disasm(sb,va):
   # detect operand immediate target / rip target in x86
   for op in ins.operands:
    if op.type==2 and op.imm==target:
      print('imm',hex(ins.address),ins.mnemonic,ins.op_str);break
    if op.type==3:
      ea=ins.address+ins.size+op.mem.disp
      if ea==target: print('mem',hex(ins.address),ins.mnemonic,ins.op_str);break
