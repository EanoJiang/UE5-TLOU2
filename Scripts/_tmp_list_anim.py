import struct,sys
p=sys.argv[1] if len(sys.argv)>1 else r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read(); magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(pct)]
def cs(o):
 if o<0 or o>=len(b):return''
 e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else''
for pi,(po,ps,fl) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0]; starts=[]
 for ei in range(ec):
  no,ro=struct.unpack_from('<QI',b,po+20+16*ei);starts.append((po+ro,ei,ro))
 for rs,ei,ro in starts:
  name=cs(po+struct.unpack_from('<Q',b,rs)[0]);typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0])
  if typ not in ('ANIM','ANIM_GROUP'):continue
  nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps]); raw=b[rs:nxt]
  vals=[]
  for off in range(0,min(200,len(raw)),8):
   q=struct.unpack_from('<Q',raw,off)[0]
   if 0<q<ps: vals.append((off,q,po+q))
  print(pi,ei,hex(ro),rs,nxt-rs,typ,repr(name),'u32_12',hex(struct.unpack_from('<I',b,rs+48)[0]),'u32_16',hex(struct.unpack_from('<I',b,rs+52)[0]),'ptrs',vals)
