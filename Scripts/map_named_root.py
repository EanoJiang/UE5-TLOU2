import struct,os,json
p=r'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak';b=open(p,'rb').read();magic,hdr,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)];
for pi,(po,ps,fl) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0]; starts=[]
 def cs(o):
  e=b.find(b'\0',o); return b[o:e].decode('utf8','replace')
 for ei in range(ec):
  no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro
  try: name=cs(po+struct.unpack_from('<Q',b,rs)[0]);typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0])
  except:continue
  starts.append((rs,ei,ro,name,typ))
 raw=[]
 for rs,ei,ro,name,typ in starts:
  if typ!='ANIM_RAWCHANNELS':continue
  nxt=min([x[0] for x in starts if x[0]>rs]+[po+ps]);c=struct.unpack_from('<I',b,rs+48)[0]
  h=[struct.unpack_from('<Q',b,rs+72+8*i)[0] for i in range(min(c,500))];ptrbase=rs+72+8*c; ptr=[struct.unpack_from('<Q',b,ptrbase+8*i)[0] for i in range(min(c,500))]
  raw.append({'rs':rs,'end':nxt,'entry':ei,'name':name,'count':c,'hashes':h,'ptrs':ptr,'page':pi,'po':po,'size':nxt-rs})
 def findraw(t):
  return next((r for r in raw if r['rs']<=t<r['end']),None)
 for rs,ei,ro,name,typ in starts:
  if typ!='ANIM':continue
  if rs+96>len(b):continue
  v=struct.unpack_from('<II',b,rs+48); p1,p2,p3,p4,p5=[struct.unpack_from('<Q',b,rs+56+8*i)[0] for i in range(5)]
  r=findraw(po+p2)
  if not r:continue
  # root hash index
  rootix=r['hashes'].index(0x509903bb65ac341e) if 0x509903bb65ac341e in r['hashes'] else None
  if rootix is None:continue
  d=po+r['ptrs'][rootix];fmt=struct.unpack_from('<I',b,d)[0] if d+12<=len(b) else 0;dp=struct.unpack_from('<Q',b,d+8)[0] if d+16<=len(b) else 0
  ds=po+dp; nd=min([po+x for x in r['ptrs'] if po+x>d]+[r['end']]); payload=b[ds:nd]
  # codec pointer p1
  ct=po+p1; cm=u32=struct.unpack_from('<I',b,ct)[0] if ct+4<=len(b) else 0
  codec={'magic':hex(cm),'offset':ct}
  if cm==0x41430102 and ct+48<=len(b):
   codec.update({'size':u32 if False else struct.unpack_from('<I',b,ct+8)[0],'groups':struct.unpack_from('<H',b,ct+12)[0],'frames':struct.unpack_from('<H',b,ct+14)[0],'rate':struct.unpack_from('<f',b,ct+28)[0],'period':struct.unpack_from('<f',b,ct+36)[0],'duration':struct.unpack_from('<f',b,ct+40)[0],'section_offset':struct.unpack_from('<I',b,ct+48)[0]})
  print('p',pi,'ANIM',ei,'name',name,'v',v,'ANIMrs',rs,'raw',r['entry'],r['rs'],'raw_count',r['count'],'rootix',rootix,'fmt',hex(fmt),'payload',len(payload),'codec',codec)
