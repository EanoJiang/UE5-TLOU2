import pefile,struct
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;img=p.get_memory_mapped_image();text=next(s for s in p.sections if s.Name.startswith(b'.text'));tb=text.get_data();targets={}
for fo in [0x30056b0,0x30056e0,0x3005708,0x3005738,0x3005768,0x3005798,0x30057c0,0x30057e0,0x3005808,0x3005830]:
 sec=next(s for s in p.sections if s.PointerToRawData<=fo<s.PointerToRawData+s.SizeOfRawData); rr=sec.VirtualAddress+fo-sec.PointerToRawData;targets[base+rr]=fo
hits={k:[] for k in targets};textva=base+text.VirtualAddress
for i in range(len(tb)-7):
 # detect rex + opcode 8d + modrm with RIP
 if tb[i] in range(0x40,0x50) and tb[i+1] in (0x8d,0x8b,0x89,0x8a,0x88,0xc7,0x03,0x2b,0x33,0x39,0x3b,0xf3,0xf0) and (tb[i+2]&0xc7)==0x05:
  disp=struct.unpack_from('<i',tb,i+3)[0];t=textva+i+7+disp
  if t in hits:hits[t].append(text.PointerToRawData+i)
 # no rex forms 8d 05
 if tb[i]==0x8d and (tb[i+1]&0xc7)==0x05:
  disp=struct.unpack_from('<i',tb,i+2)[0];t=textva+i+6+disp
  if t in hits:hits[t].append(text.PointerToRawData+i)
for t,fo in targets.items():print(hex(fo),len(hits[t]),[hex(x) for x in hits[t][:50]])
