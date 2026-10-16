from pathlib import Path
import sys,json,struct,collections
ROOT=Path(r'D:/TLOU2_UE5_8_Codex');sys.path.insert(0,str(ROOT/'Scripts'))
from ngfx_resource_reader import object_blob,object_index,read_chunk
from ngfx_descriptor_reader import parse_heap
events=json.loads((ROOT/'Exports/CaptureBuffers/frame_event_index.json').read_text());objs=json.loads((ROOT/'Exports/CaptureBuffers/initial_object_index.json').read_text())
cmds=json.loads((ROOT/'Exports/CaptureBuffers/command_recording_resource_inventory.json').read_text())['selected_commandlists'];cmdbyseq={c['sequence_id']:c for c in cmds}
heaps=[]
for ob in objs:
 if ob['type_name']!='DescriptorHeap':continue
 d=object_blob(ob['uid'],'create');inc,cpu,gpu=struct.unpack_from('<IQQ',d,len(d)-21)
 if inc not in (8,16,32,64):continue
 heaps.append({'uid':ob['uid'],'increment':inc,'cpu':cpu,'gpu':gpu})
print('GPUHEAPS',heaps)
descriptors={};bound=[];dispatches=[];count=collections.Counter();copies=0
for h in heaps:
 if h['uid'] not in [65,66,7002,7553,7560,5381,5382,5383,5384,5385,5386]:continue
 for slot,value in parse_heap(h['uid'])['entries'].items():
  descriptors[h['cpu']+slot*h['increment']]={**value,'sequence':-1,'source_cpu':h['cpu']+slot*h['increment'],'initial_heap_uid':h['uid']}
for ev in sorted(events,key=lambda e:e['sequence']):
 data=read_chunk(ev['chunk'])[ev['offset']:ev['offset']+ev['size']];fn=ev['function_name']
 if fn=='ID3D12Device_CreateConstantBufferView' and len(data)==28:
  tag,addr,size,dest,tail=struct.unpack('<IQIQI',data)
  if tag==0xfa000004:
   descriptors[dest]={'kind':'CBV','address':addr,'size':size,'sequence':ev['sequence'],'source_cpu':dest};count['cbv']+=1
 elif fn=='ID3D12Device_CreateShaderResourceView' and len(data)==56:
  uid,tag,fmt,dim,mapping,first,num,stride,flags,dest,tail=struct.unpack('<Q4IQ3IQI',data)
  if tag==0xfa000004 and dim==1:
   descriptors[dest]={'kind':'SRV','resource_uid':uid,'format':fmt,'first_element':first,'num_elements':num,'stride':stride,'flags':flags,'sequence':ev['sequence'],'source_cpu':dest};count['srvbuffer']+=1
 elif fn=='ID3D12Device_CopyDescriptorsSimple' and len(data)==32:
  num,dest,d0,src,s0,ht=struct.unpack('<IQIQII',data)
  inc=32 if ht in (0,1) else 8
  for index in range(num):
   source=descriptors.get(src+index*inc)
   if source:descriptors[dest+index*inc]=source;copies+=1
   else:descriptors.pop(dest+index*inc,None)
 elif fn=='CommandRecording' and ev['sequence'] in cmdbyseq:
  c=cmdbyseq[ev['sequence']]
  if 'deformer' not in c['name']:continue
  pso=None;tables={}
  for cmd in c['commands']:
   arg=bytes.fromhex(cmd['args_hex']);fid=cmd['function_id']
   if fid==51:pso=struct.unpack_from('<Q',arg)[0]
   if fid==40:
    dispatches.append({'sequence':ev['sequence'],'commandlist_uid':c['commandlist_uid'],'name':c['name'],'command_index':cmd['index'],'pipeline_uid':pso,'dispatch_xyz':list(struct.unpack('<3I',arg)),'tables':{str(i):t for i,t in tables.items()}})
   if fid!=57:continue
   rootparam,gpu,tail=struct.unpack('<IQI',arg)
   heap=next((h for h in heaps if h['gpu'] and 0<=gpu-h['gpu']<0x2000000),None)
   cpu=heap['cpu']+gpu-heap['gpu'] if heap else None
   slots=[descriptors.get(cpu+i*32) for i in range(16)] if cpu is not None else[]
   record={'sequence':ev['sequence'],'commandlist_uid':c['commandlist_uid'],'name':c['name'],'command_index':cmd['index'],'pso':pso,'root_parameter':rootparam,'gpu_handle':gpu,'heap':heap,'cpu_handle':cpu,'slots':slots}
   bound.append(record);tables[rootparam]=record
out=ROOT/'Exports/CaptureBuffers/deformer_descriptor_bindings_probe.json';out.write_text(json.dumps({'counts':dict(count),'resolved_copies':copies,'bindings':bound,'dispatches':dispatches},indent=2))
print('COUNTS',count,'copies',copies,'bindings',len(bound),'resolved',sum(any(s for s in b['slots']) for b in bound),'out',out)
for b in bound:
 if b['root_parameter']==3:print(b['sequence'],b['command_index'],b['name'],b['root_parameter'],[(i,s) for i,s in enumerate(b['slots'][:3]) if s])
