import struct,collections,os,math
root=0x509903bb65ac341e
for p in [r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak',r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-mm-explore\source.pak',r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-mm-tense\source.pak',r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-gestures\source.pak']:
 b=open(p,'rb').read();_,_,_,_,_,pt,pc,*_=struct.unpack_from('<11I',b,0); forms=collections.Counter(); samples=collections.Counter(); ex=[]
 for pi,(po,ps,_) in enumerate([struct.unpack_from('<3I',b,pt+12*i) for i in range(pc)]):
  if po+20>len(b):continue
  n=struct.unpack_from('<H',b,po+18)[0]
  for ei in range(n):
   q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
   try: cnt=struct.unpack_from('<I',b,rs+48)[0];hr=struct.unpack_from('<Q',b,rs+56)[0];dr=struct.unpack_from('<Q',b,rs+64)[0]
   except:continue
   if cnt<=0 or cnt>500 or po+hr+cnt*8>len(b) or po+dr+cnt*8>len(b):continue
   hs=[struct.unpack_from('<Q',b,po+hr+8*i)[0] for i in range(cnt)];ds=[struct.unpack_from('<Q',b,po+dr+8*i)[0] for i in range(cnt)]
   if root not in hs:continue
   j=hs.index(root);d=po+ds[j];fmt=struct.unpack_from('<I',b,d)[0];dp=struct.unpack_from('<Q',b,d+8)[0];dps=[]
   for x in ds:
    dd=po+x
    if dd+16<=len(b):dps.append(struct.unpack_from('<Q',b,dd+8)[0])
   nxt=min([x for x in dps if x>dp] or [ps]);nb=nxt-dp
   if nb<=0 or nb%2:continue
   vals=[struct.unpack_from('<e',b,po+dp+2*k)[0] for k in range(nb//2)]
   ar=1 if (fmt&0xff0000)==0xf70000 else 2 if (fmt&0xff0000)==0xfb0000 else None
   forms[hex(fmt)] += 1
   if ar:
    nsm=(len(vals)-16)//ar if len(vals)>=16 and (len(vals)-16)%ar==0 else -1
    samples[(hex(fmt),nsm)] +=1
    if len(ex)<15: ex.append((pi,ei,hex(fmt),nb,nsm,vals[:12],vals[-12:]))
 print('\n',os.path.basename(p),'forms',forms,'samples',samples,'examples',ex[:5])
