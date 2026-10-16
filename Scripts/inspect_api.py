import unreal
sm=unreal.load_asset('/Game/TLOU2/ExactStatic/SM_patrol_jacket__lod0_LODShape0_shader1_merged_partition0')
unreal.log('APIS '+str([x for x in dir(sm) if 'mat' in x.lower() or 'slot' in x.lower() or 'editor' in x.lower()]))
a=sm.get_editor_property('static_materials')[0]
unreal.log('STATICMAT_APIS '+str([x for x in dir(a) if 'mat' in x.lower() or 'slot' in x.lower() or 'editor' in x.lower()]))
