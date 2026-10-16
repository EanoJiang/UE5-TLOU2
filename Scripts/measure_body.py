import bpy
objs=[o for o in bpy.data.objects if o.type=='MESH']
mins=[1e9]*3;maxs=[-1e9]*3
for o in objs:
 for v in o.bound_box:
  p=o.matrix_world@__import__('mathutils').Vector(v)
  for i in range(3): mins[i]=min(mins[i],p[i]);maxs[i]=max(maxs[i],p[i])
print('BOUNDS',mins,maxs,'HEIGHT',maxs[2]-mins[2])
