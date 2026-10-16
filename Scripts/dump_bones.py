import bpy,json
for a in bpy.data.armatures:
 print(a.name,len(a.bones)); print([b.name for b in a.bones[:30]])
