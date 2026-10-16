import unreal
p='/Game/TLOU2/Probe1074/Ellie_1074_SkeletonProbe'; a=unreal.load_asset(p); s=a.get_editor_property('skeleton') if a else None
unreal.log('ASSET '+str(a)+' SKELETON '+str(s))
unreal.log('SKDIR '+str([x for x in dir(s) if 'bone' in x.lower() or 'ref' in x.lower()]))
unreal.log('MSHDIR '+str([x for x in dir(a) if 'skeleton' in x.lower() or 'bone' in x.lower()]))
unreal.log('PROBE_VERIFY_DONE')
