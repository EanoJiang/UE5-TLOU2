import struct,pathlib
p=pathlib.Path(r'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak');b=p.read_bytes();po=9541328;psz=1045200;ec=struct.unpack_from('<H',b,po+18)[0];print('ec',ec)
def cstr(o):
 e=b.find(b'\0',o);return b[o:e].decode('utf-8','replace')
for ei in range(ec):
 q=po+20+16*ei
 no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
 try:n=cstr(po+struct.unpack_from('<Q',b,rs)[0]);t=cstr(po+struct.unpack_from('<Q',b,rs+8)[0])
 except:continue
 if ei>180 and ei<700 and t in ['ANIM','ANIM_GROUP','ANIM_RAWCHANNELS']:
  print(ei,hex(ro),hex(rs-po),t,n)
