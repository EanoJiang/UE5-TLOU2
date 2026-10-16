import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();h,hd,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]
def cs(o):
 e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else ''
for pi,(po,ps,_) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0]
 for ei in range(ec):
  no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro; name=cs(po+struct.unpack_from('<Q',b,rs)[0]);typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0])
  if typ!='ANIM_GROUP':continue
  nxt=po+ps
  for ej in range(ec):
   _,rr=struct.unpack_from('<QI',b,po+20+16*ej);xx=po+rr
   if xx>rs:nxt=min(nxt,xx)
  raw=b[rs:nxt]; print('GROUP',pi,ei,hex(ro),rs,nxt-rs,repr(name)); print(raw[:128].hex(' '));
  for off in range(0,min(len(raw),512),8):
   q=struct.unpack_from('<Q',raw,off)[0]
   if 0<q<ps:print(' ptr',off,hex(q),'abs',po+q,'str',repr(cs(po+q)[:80]))
