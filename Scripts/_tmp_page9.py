import struct
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak';b=open(p,'rb').read();h,hd,li,lo,n,pt,fp,fo,*_=struct.unpack_from('<11I',b,0);pages=[struct.unpack_from('<3I',b,pt+12*i) for i in range(n)]
def cs(o):e=b.find(b'\0',o);return b[o:e].decode('utf8','replace') if e>=0 else''
pi=9;po,ps,_=pages[pi];ec=struct.unpack_from('<H',b,po+18)[0];print('po',po,'ps',ps,'ec',ec)
for ei in range(180,240):
 q=po+20+16*ei;no,ro=struct.unpack_from('<QI',b,q);rs=po+ro
 name=cs(po+struct.unpack_from('<Q',b,rs)[0]);typ=cs(po+struct.unpack_from('<Q',b,rs+8)[0]); print(ei,hex(ro),rs,typ,repr(name), 'u32', [hex(struct.unpack_from('<I',b,rs+4*k)[0]) for k in range(14,18)])
