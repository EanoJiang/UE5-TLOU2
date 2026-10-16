import bpy, json

# Blender 5.2 uses layered Actions: F-curves live in a strip's
# ActionChannelbag, while older versions exposed them as Action.fcurves.
p=r'D:/TLOU2_UE5_8_Codex/Exports/Ellie_1074_RootMotion_AnimationProbe.fbx'
out_path=r'D:/TLOU2_UE5_8_Codex/Exports/rootmotion_fbx_verification.json'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=p, use_anim=True)

def action_fcurves(action):
    if hasattr(action, 'fcurves'):
        return list(action.fcurves)
    out=[]
    for layer in getattr(action, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            for bag in getattr(strip, 'channelbags', []):
                out.extend(list(getattr(bag, 'fcurves', [])))
    return out

def curve_record(fc):
    vals=[float(k.co[1]) for k in fc.keyframe_points]
    return {'path':fc.data_path,'axis':int(fc.array_index),'keys':len(vals),
            'min':min(vals) if vals else None,'max':max(vals) if vals else None,
            'first':vals[0] if vals else None,'last':vals[-1] if vals else None}

rows=[]
for ob in bpy.data.objects:
    if ob.type!='ARMATURE':
        continue
    action=ob.animation_data.action if ob.animation_data else None
    curves=action_fcurves(action) if action else []
    roots=[fc for fc in curves if fc.data_path in ('location','pose.bones["root"].location')]
    rows.append({'name':ob.name,'bones':len(ob.data.bones),
                 'animation_data':bool(ob.animation_data),
                 'action':action.name if action else None,
                 'frame_range':list(action.frame_range) if action else [],
                 'fcurves':len(curves),
                 'root_motion_curves':[curve_record(fc) for fc in roots]})

out={'file':p,'objects':rows,
     'actions':[{'name':a.name,'frame_range':list(a.frame_range),
                 'fcurves':len(action_fcurves(a))} for a in bpy.data.actions]}
json.dump(out,open(out_path,'w'),indent=2)
print('ROOTMOTION_FBX_VERIFY',json.dumps(out))
