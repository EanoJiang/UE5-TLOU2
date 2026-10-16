import struct
p=r'D:\TLOU2_UE5_8_Codex\Content\TLOU2\SourcePaks\ellie-skel.pak';b=open(p,'rb').read(); print('len',len(b),b[:64].hex())
magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); print(magic,hdr,pct,pt,fp,fo); pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(pct)]
def cstr(o):
 if o<0 or o>=len(b):return ''
 e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else ''
for pi,(po,ps,fl) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0]; print('\nPAGE',pi,'po',po,'ps',ps,'flags',fl,'ec',ec)
 starts=[]
 for ei in range(ec):
  q=po+20+16*ei; no,ro=struct.unpack_from('<QI',b,q);rs=po+ro;starts.append((rs,ei,ro));
 for rs,ei,ro in starts:
  try:name=cstr(po+struct.unpack_from('<Q',b,rs)[0]);typ=cstr(po+struct.unpack_from('<Q',b,rs+8)[0])
  except:continue
  nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps]); print(ei,'rel',hex(ro),'rs',rs,'size',nxt-rs,'name',name,'typ',typ,'head',b[rs:rs+32].hex())
  if typ in ('JOINT_HIERARCHY','SKELETON','BONE','JOINT'):
   raw=b[rs:nxt]
   print('u32',[hex(struct.unpack_from('<I',raw,4*i)[0]) for i in range(min(32,len(raw)//4))])
   print('u64',[hex(struct.unpack_from('<Q',raw,8*i)[0]) for i in range(min(32,len(raw)//8))])
