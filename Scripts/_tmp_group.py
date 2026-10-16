import struct, json
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak';b=open(p,'rb').read(); po,ps,_=struct.unpack_from('<3I',b,1088+12); # wait page table at 44 and page index? 
# use page list
magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(pct)]
def cstr(o):
 e=b.find(b'\0',o);return b[o:e].decode('utf8','replace')
for pi,(po,ps,_) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0]
 starts=[]
 for ei in range(ec):
  no,ro=struct.unpack_from('<QI',b,po+20+16*ei); starts.append((po+ro,ei,ro))
 for rs,ei,ro in starts:
  name=cstr(po+struct.unpack_from('<Q',b,rs)[0]);typ=cstr(po+struct.unpack_from('<Q',b,rs+8)[0]);
  if typ!='ANIM_GROUP':continue
  nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps]); print('GROUP',pi,ei,'rs',rs,'size',nxt-rs,'name',name,typ); raw=b[rs:nxt]
  print('hex',raw.hex(' '))
  print('u32',[(i*4,hex(struct.unpack_from('<I',raw,i*4)[0])) for i in range(min(len(raw)//4,80))])
  print('u64',[(i*8,hex(struct.unpack_from('<Q',raw,i*8)[0])) for i in range(min(len(raw)//8,40))])
  # page-relative pointer-looking words; print strings at all candidate absolute offsets
  for i in range(0,len(raw)-8,8):
   v=struct.unpack_from('<Q',raw,i)[0]
   if 0<v<ps and po+v<len(b):
    target=po+v
    st=cstr(target)
    print(' ptr',i,hex(v),'abs',target,'str',repr(st[:100]))
