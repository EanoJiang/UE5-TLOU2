import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);pi=6;po,ps,_=struct.unpack_from('<3I',b,pt+12*pi);n=struct.unpack_from('<H',b,po+18)[0]
print('page6 po',po,'size',ps,'entries',n)
for ei in range(n):
 q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
 try:nptr,tptr=struct.unpack_from('<QQ',b,rs);name=b[po+nptr:b.find(b'\0',po+nptr)].decode();typ=b[po+tptr:b.find(b'\0',po+tptr)].decode()
 except:continue
 print(ei,'rs_rel',hex(ro),'rs',rs,'name',name,'typ',typ,'head',b[rs+48:rs+80].hex(' '))
