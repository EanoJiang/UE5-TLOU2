import bpy,csv,json,os,math
ROOT=r'D:\TLOU2_UE5_8_Codex'
CSV_PATH=os.path.join(ROOT,'Exports','AnimationSources','DecodedRawChannels','named_root_trajectory_samples.csv')
TARGET='ellie-prone-lg-aim-strafe-0-fw'
rows=[]
with open(CSV_PATH,newline='',encoding='utf8') as f:
 for r in csv.DictReader(f):
  if r['anim_name']==TARGET and r['source']=='anim-ellie-player-movement.pak': rows.append(r)
rows.sort(key=lambda r:int(r['sample_index']))
if not rows: raise RuntimeError('trajectory clip not found')
armobj=next((o for o in bpy.data.objects if o.type=='ARMATURE'),None)
if armobj is None: raise RuntimeError('no armature in source blend')
if 'root' not in armobj.data.bones: raise RuntimeError('root bone not found')
act=bpy.data.actions.new('RAW_Candidate_'+TARGET)
act.use_fake_user=True
path='pose.bones["root"].location'
for idx in range(3):
 fc=act.fcurves.new(path,index=idx,action_group='RAW_ROOT_CANDIDATE')
 fc.keyframe_points.add(len(rows))
 for i,r in enumerate(rows):
  # Raw paired stream is kept in source units.  Axis assignment is an explicit
  # interchange convention; source units/interpolation are unresolved.
  val=float(r['value0']) if idx==0 else float(r['value1']) if idx==1 else 0.0
  fc.keyframe_points[i].co=(i+1,val)
  fc.keyframe_points[i].interpolation='LINEAR'
 fc.update()
armobj.animation_data_create(); armobj.animation_data.action=act
sc=bpy.context.scene;sc.render.fps=30;sc.render.fps_base=1.0;sc.frame_start=1;sc.frame_end=len(rows)
meta={'clip':TARGET,'source':'anim-ellie-player-movement.pak','raw_hash':'0x509903bb65ac341e','format':rows[0]['root_format'],'codec_frames':int(rows[0]['codec_frames']),'sample_count':len(rows),'sample_rate':30.0,'sample_period_s':1.0/30.0,'source_reported_sample_rate':float(rows[0]['codec_sample_rate']),'axis_interchange':'value0 -> root.location.x; value1 -> root.location.y; z=0','units':'unresolved source half-float units','interpolation':'linear only for interchange preview','status':'raw root trajectory candidate; not claimed as exact bone animation'}
outblend=os.path.join(ROOT,'Blender','Ellie_RawRootCandidate_'+TARGET.replace('-','_')+'.blend');os.makedirs(os.path.dirname(outblend),exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=outblend)
json.dump(meta,open(os.path.join(ROOT,'Exports','raw_root_candidate_metadata.json'),'w',encoding='utf8'),indent=2)
print('RAW_ROOT_CANDIDATE',outblend,'frames',len(rows),'format',rows[0]['root_format'])
