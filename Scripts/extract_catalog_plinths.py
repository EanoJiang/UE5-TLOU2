ROOT='D:/TLOU2_UE5_8_Codex'
code=open(ROOT+'/Scripts/extract_nd_pak_fake.py').read();a=code.index("packages=['ellie-skel.pak'");b=code.index('\n',a)
code=code[:a]+"packages=['ellie-skel.pak','keyart-turntable-wet-large.pak','keyart-turntable-wood-small.pak','keyart-turntable-fg.pak','keyart-turntable-concrete-large.pak']"+code[b:]
exec(compile(code,ROOT+'/Scripts/extract_nd_pak_fake.py','exec'))
