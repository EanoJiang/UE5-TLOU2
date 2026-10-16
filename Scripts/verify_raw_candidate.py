import bpy
for a in bpy.data.actions:
 if a.name.startswith('RAW_Candidate'):
  print('ACTION',a.name,len(a.fcurves),a.frame_range)
  for f in a.fcurves: print(f.data_path,f.array_index,len(f.keyframe_points),f.keyframe_points[0].co[:],f.keyframe_points[-1].co[:])
