import struct, os, json, math
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read()
_,_,_,_,_,pt,fp,fo,*_=struct.unpack_from('<11I',b,0)
# print header all ints
print('header',struct.unpack_from('<11I',b,0))
pages=[struct.unpack_from('<3I',b,pt+p*12) for p in range(fp)]
root=0x509903bb65ac341e
rows=[]
for pi,(po,ps,fl) in enumerate(pages):
  try: n=struct.unpack_from('<H',b,po+18)[0]
  except: continue
  for j in range(n):
    q=po+20+j*16; no,ro=struct.unpack_from('<QI',b,q); rs=po+ro
    try: name_off,typ_off=struct.unpack_from('<QQ',b,rs); name=b.find(b'\0',po+name_off); typ_end=b.find(b'\0',po+typ_off); typ=b[po+typ_off:typ_end].decode('utf8','replace')
    except Exception as e: continue
    if typ!='ANIM_RAWCHANNELS': continue
    cnt=struct.unpack_from('<I',b,rs+48)[0]; hrel=struct.unpack_from('<Q',b,rs+56)[0]; drel=struct.unpack_from('<Q',b,rs+64)[0]
    if cnt>2000 or po+hrel+cnt*8>len(b) or po+drel+cnt*8>len(b): continue
    hashes=[struct.unpack_from('<Q',b,po+hrel+8*i)[0] for i in range(cnt)]
    descs=[struct.unpack_from('<Q',b,po+drel+8*i)[0] for i in range(cnt)]
    if root in hashes:
      idx=hashes.index(root); d=po+descs[idx]; fmt=struct.unpack_from('<I',b,d)[0]; dp=struct.unpack_from('<Q',b,d+8)[0]; data=po+dp
      # descriptor data first bytes/half
      vals=[]
      for k in range(min(64,(len(b)-data)//2)):
        vals.append(struct.unpack_from('<e',b,data+2*k)[0])
      # identify descriptor starts from raw data first words
      rows.append(dict(page=pi,entry=j,po=po,rs=rs,cnt=cnt,idx=idx,fmt=fmt,desc_rel=descs[idx],data_rel=dp,data_abs=data,head=b[data:data+64].hex(' '),half=vals[:32]))
print('rows',len(rows))
for r in rows:
 print(json.dumps({k:r[k] for k in ('page','entry','cnt','idx','fmt','data_rel','data_abs','half')},separators=(',',':')))
out=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_descriptor_index.json'; json.dump(rows,open(out,'w'),indent=2)
print('wrote',out)
