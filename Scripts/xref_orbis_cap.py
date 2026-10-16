import pefile,time
from capstone import *
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;img=p.get_memory_mapped_image();text=next(s for s in p.sections if s.Name.startswith(b'.text'));rva=text.VirtualAddress;code=img[rva:rva+text.Misc_VirtualSize];targets={}
for fo in [0x30056b0,0x30056e0,0x3005708,0x3005738,0x3005768,0x3005798,0x30057c0,0x30057e0,0x3005808,0x3005830]:
 sec=next(s for s in p.sections if s.PointerToRawData<=fo<s.PointerToRawData+s.SizeOfRawData); rr=sec.VirtualAddress+fo-sec.PointerToRawData;targets[base+rr]=fo
hits={k:[] for k in targets};md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True;md.skipdata=True
st=time.time()
for ins in md.disasm(code,base+rva):
 if ins.mnemonic=='.byte': continue
 try: ops=ins.operands
 except: continue
 for op in ops:
  if op.type==2 and op.mem.base==41:
   t=ins.address+ins.size+op.mem.disp
   if t in hits:hits[t].append(ins.address)
  elif op.type==1 and op.imm in hits:hits[op.imm].append(ins.address)
print('elapsed',time.time()-st)
for t,fo in targets.items():print(hex(fo),len(hits[t]),[hex(x-base) for x in hits[t][:30]])
