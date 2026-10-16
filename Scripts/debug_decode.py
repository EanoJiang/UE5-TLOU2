import sys,time;sys.path.insert(0,'Scripts');import decode_root_candidate_tracks as d
p=r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\raw\anim-ellie-player-movement\source.pak'; b=open(p,'rb').read();_,_,_,_,_,pt,fp,*_=d.read_header(b); pages=[__import__('struct').unpack_from('<3I',b,pt+12*i) for i in range(fp)]
print('loaded',len(b),fp)
t=time.time(); c=d.find_codec_rates(b,pages); print('codecs',len(c),time.time()-t)
