import struct,glob,os,re,json
ROOT=r'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97'
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def cstr(b,o):
 if o<0 or o>=len(b): return ''
 e=b.find(b'\0',o); e=len(b) if e<0 else e
 try:return b[o:e].decode('utf8','replace')
 except:return ''
def parse(b):
 # find starts of ANIMMAGICSTR and infer prefix hash
 poss=[]; i=0
 while 1:
  i=b.find(b'ANIMMAGICSTR',i)
  if i<0:break
  poss.append(max(0,i-4)); i+=1
 out=[]
 for ix,s in enumerate(poss):
  e=poss[ix+1] if ix+1<len(poss) else len(b)
  cb=b[s+16:e]
  try:
   magic,hdr,loginidx,loginoff,pct,pt,fixpages,fixoff,unk5,unk6,unk7=struct.unpack_from('<11I',cb,0)
   if magic not in (2681,2685,68217,2147486329,68221): continue
   pages=[]
   for p in range(pct): pages.append(struct.unpack_from('<3I',cb,pt+p*12))
   # page header entries each page
   items=[]
   for p,(po,ps,_) in enumerate(pages):
    if po+20>len(cb):continue
    # page has unknown 12 then size u32 at +12, flags u16 +14, entry count u16 +16
    n=struct.unpack_from('<H',cb,po+18)[0]
    for j in range(n):
     q=po+20+j*20
     if q+20>len(cb):continue
     no,ro=struct.unpack_from('<QI',cb,q+0)
     # pointer likely q values relative page start; offsets can be > cb
     name=cstr(cb,po+no)
     # resource offset relative page start
     rs=po+ro
     if rs+16<=len(cb):
      ino=struct.unpack_from('<Q',cb,rs)[0]; it=struct.unpack_from('<Q',cb,rs+8)[0]
      iname=cstr(cb,po+ino); itype=cstr(cb,po+it)
     else: iname=itype=''
     items.append((name,ro,iname,itype,rs))
   out.append(dict(idx=ix,start=s,end=e,size=len(cb),magic=magic,hdr=hdr,pages=pages,items=items))
  except Exception as ex:
   out.append(dict(idx=ix,start=s,end=e,size=len(cb),error=str(ex)))
 return out

for p in glob.glob(ROOT+'\\*.stm'):
 b=open(p,'rb').read(); ps=parse(b)
 print('\n',os.path.basename(p),len(b),'chunks',len(ps))
 for x in ps[:3]: print(' chunk',x['idx'],'size',x['size'],'pages',x.get('pages'),'items',[(z[0],z[2],z[3]) for z in x.get('items',[])][:20],x.get('error'))
