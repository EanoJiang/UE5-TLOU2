import struct, json, os, re

def cstr(b,o):
 e=b.find(b'\0',o)
 return b[o:e].decode('utf8','replace') if e>=0 else ''
def parse(p):
 b=open(p,'rb').read(); magic,hdr,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]; out=[]
 for pi,(po,ps,fl) in enumerate(pages):
  ec=struct.unpack_from('<H',b,po+18)[0]
  for ei in range(ec):
   q=po+20+16*ei
   if q+16>len(b):continue
   no,ro=struct.unpack_from('<QI',b,q); rs=po+ro
   if rs+16>len(b):continue
   try:name=cstr(b,po+struct.unpack_from('<Q',b,rs)[0]); typ=cstr(b,po+struct.unpack_from('<Q',b,rs+8)[0])
   except:continue
   if typ not in ('ANIM_RAWCHANNELS','ANIM','ANIM_GROUP'):continue
   # resource next start among all entries in page or page end
   starts=[]
   for ej in range(ec):
    qq=po+20+16*ej
    try:_,rr=struct.unpack_from('<QI',b,qq); starts.append(po+rr)
    except:pass
   nxt=min([x for x in starts if x>rs]+[po+ps])
   raw=b[rs:min(rs+256,nxt)]
   words=[struct.unpack_from('<Q',b,rs+8*i)[0] for i in range(min(32,max(0,(nxt-rs)//8)))]
   # pointers from first 32 qwords likely page relative
   ptr=[{'raw':v,'target':po+v,'in_page':0<=v<ps and po+v<len(b),'delta':(po+v-rs)} for v in words if 0<v<ps]
   out.append(dict(page=pi,entry=ei,po=po,ps=ps,rs=rs,ro=ro,next=nxt,size=nxt-rs,name=name,typ=typ,raw=raw.hex(),u32=[struct.unpack_from('<I',b,rs+4*i)[0] for i in range(min(64,(nxt-rs)//4))],u64=words,ptr=ptr))
 print(json.dumps(dict(file=os.path.basename(p),size=len(b),pages=pages,res=out),indent=2))
for p in [r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak',r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak']:
 parse(p)
