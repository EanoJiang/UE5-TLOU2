ROOT='D:/TLOU2_UE5_8_Codex'
code=open(ROOT+'/Scripts/extract_catalog_plinths.py').read();code=code.replace("exec(compile(code,ROOT+'/Scripts/extract_nd_pak_fake.py','exec'))","code=code.replace(\"if skel: pak.boneList=skel.boneList; pak.boneMap=skel.boneMap; pak.boneDict=skel.boneDict\",\"if skel and not fname.startswith('keyart'): pak.boneList=skel.boneList; pak.boneMap=skel.boneMap; pak.boneDict=skel.boneDict\")\nexec(compile(code,ROOT+'/Scripts/extract_nd_pak_fake.py','exec'))")
exec(compile(code,ROOT+'/Scripts/extract_catalog_plinths.py','exec'))
