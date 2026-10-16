import json, collections, pathlib, math
p=pathlib.Path(r'Exports/AnimationSources/DecodedRawChannels/rawchannels_decode_manifest.json'); d=json.loads(p.read_text())
fmt=collections.Counter(); bysrc=collections.Counter(); dynamic=[]; static=[]
for src in d.get('sources',[]):
 for r in src.get('records',[]):
  for c in r.get('channels',[]):
   if not c.get('root_candidate') or 'error' in c: continue
   fmt[c.get('format')]+=1; bysrc[r['source']]+=1
   if c.get('dynamic_half_count',0):
    dynamic.append({'source':r['source'],'page':r['page'],'entry':r['entry'],'resource_offset':r['resource_offset'],'format':c.get('format'),'payload_bytes':c.get('payload_bytes'),'dynamic_half_count':c.get('dynamic_half_count'),'observed_dimension':c.get('dynamic_dimension_observed'),'baseline_half':c.get('baseline_half'),'dynamic_stats':c.get('dynamic_stats')})
   else: static.append({'source':r['source'],'page':r['page'],'entry':r['entry'],'resource_offset':r['resource_offset'],'format':c.get('format'),'baseline_half':c.get('baseline_half')})
out={'tool':'decode_nd_rawchannels.py','root_hash':d['root_candidate_hash'],'resources':d['resource_count'],'channels':d['channel_count'],'root_channels':d['root_channel_count'],'root_static_count':len(static),'root_dynamic_count':len(dynamic),'format_counts':dict(fmt),'source_root_counts':dict(bysrc),'dynamic_half_total':sum(x['dynamic_half_count'] for x in dynamic),'dynamic_records':dynamic[:256], 'status':'raw half streams only; no units, interpolation, or bone mapping'}
outp=pathlib.Path('Exports/AnimationSources/DecodedRawChannels/root_trajectory_summary.json');outp.write_text(json.dumps(out,indent=2)); print(json.dumps({'out':str(outp),'formats':dict(fmt),'dynamic':len(dynamic),'static':len(static),'half_total':out['dynamic_half_total']},indent=2))
