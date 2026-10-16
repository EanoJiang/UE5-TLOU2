import json,collections,struct,math,os
rows=json.load(open(r'D:\TLOU2_UE5_8_Codex\Exports\AnimationSources\movement_root_descriptor_index.json'))
for fmt,rs in sorted((k,list(g)) for k,g in __import__('itertools').groupby(sorted(rows,key=lambda x:x['fmt']),key=lambda x:x['fmt'])):
 print(hex(fmt), 'n',len(rs), 'cnts',sorted(set(x['cnt'] for x in rs)), 'pages',sorted(set(x['page'] for x in rs)), 'datalens?')
 for x in rs[:4]: print(' ',x['page'],x['entry'],'cnt',x['cnt'],'idx',x['idx'],'data',hex(x['data_rel']),'half',x['half'][:24])
