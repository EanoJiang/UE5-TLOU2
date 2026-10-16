import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=struct.unpack_from('<11I',b,0);po,ps,_=struct.unpack_from('<3I',b,pt+6*12);n=struct.unpack_from('<H',b,po+18)[0]
for ei in range(n):
 q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
 try:nptr,tptr=struct.unpack_from('<QQ',b,rs);name=b[po+nptr:b.find(b'\0',po+nptr)].decode();typ=b[po+tptr:b.find(b'\0',po+tptr)].decode()
 except:continue
 if typ!='ANIM':continue
 print('ANIM',ei,name,'rs',rs,'rel',hex(ro))
 for off in range(0,0x100,4):
  u=struct.unpack_from('<I',b,rs+off)[0]; s=struct.unpack_from('<i',b,rs+off)[0]; f=struct.unpack_from('<f',b,rs+off)[0]
  print(f'+{off:02x} u={u:08x} s={s} f={f:.8g}')
 break
