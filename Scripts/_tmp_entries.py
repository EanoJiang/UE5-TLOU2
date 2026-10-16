import struct,json
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-bindpose\source.pak';b=open(p,'rb').read(); magic,hdr,li,lo,pct,pt,fp,fo,*_=struct.unpack_from('<11I',b,0); pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(pct)]
def cstr(o):
 e=b.find(b'\0',o); return b[o:e].decode('utf8','replace') if e>=0 else ''
for pi,(po,ps,_) in enumerate(pages):
 ec=struct.unpack_from('<H',b,po+18)[0];print('PAGE',pi,po,ps,ec)
 for ei in range(ec):
  no,ro=struct.unpack_from('<QI',b,po+20+16*ei);rs=po+ro
  try:name=cstr(po+struct.unpack_from('<Q',b,rs)[0]);typ=cstr(po+struct.unpack_from('<Q',b,rs+8)[0])
  except:continue
  print(ei,'rs',rs,'rel',hex(ro),'name',name,'typ',typ,'head',b[rs:rs+16].hex())
