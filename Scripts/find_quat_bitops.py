import pefile,time
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;img=p.get_memory_mapped_image();text=next(s for s in p.sections if s.Name.startswith(b'.text'));code=img[text.VirtualAddress:text.VirtualAddress+text.Misc_VirtualSize];md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True;md.skipdata=True;hits=[];st=time.time()
for ins in md.disasm(code,base+text.VirtualAddress):
 if ins.mnemonic in ('and','test','movzx','shr','shl','sar','imul') and any('0x7fff' in op or '0x3fff' in op or '0x1fff' in op for op in ins.op_str):hits.append((ins.address-base,ins.mnemonic,ins.op_str))
print('elapsed',time.time()-st,'count',len(hits));print(hits[:300])
