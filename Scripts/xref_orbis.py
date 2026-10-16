import pefile,struct
p=pefile.PE(r'D:/Steam/steamapps/common/The Last of Us Part II/tlou-ii.exe');base=p.OPTIONAL_HEADER.ImageBase;img=p.get_memory_mapped_image();text=next(s for s in p.sections if s.Name.startswith(b'.text'));tb=text.get_data();targets={}
for fo in [0x30056b0,0x30056e0,0x3005708,0x3005738,0x3005768,0x3005798,0x30057c0,0x30057e0,0x3005808,0x3005830]:
 sec=next(s for s in p.sections if s.PointerToRawData<=fo<s.PointerToRawData+s.SizeOfRawData); rva=sec.VirtualAddress+fo-sec.PointerToRawData;targets[base+rva]=fo
print('targets',[(hex(k),hex(v)) for k,v in targets.items()]);hits={k:[] for k in targets}
for i in range(len(tb)-4):
 rel=struct.unpack_from('<i',tb,i+1)[0]; cand=base+text.VirtualAddress+i+5+rel
 if cand in hits:hits[cand].append(text.PointerToRawData+i)
for k,v in hits.items():print(hex(targets[k]),[hex(x) for x in v[:50]],'n',len(v))
