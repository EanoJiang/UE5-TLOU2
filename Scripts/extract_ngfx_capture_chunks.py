"""Recover exact LZ4/raw container payloads from an owned Nsight capture.

The file has a 24-byte `done` footer pointing to a 48-byte-entry directory.
Each entry repeats the on-disk chunk header. IDs are container chunk IDs,
not Direct3D resource IDs. This extractor does not require GPU replay.
"""
from pathlib import Path
import csv,hashlib,json,mmap,struct,time
import lz4.block

ROOT=Path(r'D:/TLOU2_UE5_8_Codex')
CAPTURE=Path(r'D:/Unpack_3A/TLOU2/Captures/NsightCapturesRetry2/tlou-ii_2026_10_16_01_55_52.ngfx-capture')
OUT=ROOT/'Exports/CaptureBuffers'
ENTRY=struct.Struct('<4sIII4Q')

class CaptureContainer:
    def __init__(self,path=CAPTURE):
        self.path=Path(path);self.handle=self.path.open('rb');self.data=mmap.mmap(self.handle.fileno(),0,access=mmap.ACCESS_READ)
        magic,self.footer_version,count,self.directory_offset=struct.unpack_from('<4sIQQ',self.data,len(self.data)-24)
        if magic!=b'enod':raise ValueError('missing done footer')
        if self.directory_offset+count*ENTRY.size!=len(self.data)-24:raise ValueError('directory bounds')
        self.records={}
        for i in range(count):
            raw=bytes(self.data[self.directory_offset+i*48:self.directory_offset+(i+1)*48])
            magic,version,flags,compression,compressed_bytes,decoded_bytes,chunk_id,offset=ENTRY.unpack(raw)
            if magic!=b'elif' or version!=1 or compression not in (0,1):raise ValueError(('chunk header',i))
            payload_bytes=compressed_bytes if compression else decoded_bytes
            if offset<4 or offset+48+payload_bytes>self.directory_offset:raise ValueError(('chunk payload bounds',chunk_id))
            header=ENTRY.unpack_from(self.data,offset)
            if header[:2]!=ENTRY.unpack(raw)[:2] or header[3:]!=ENTRY.unpack(raw)[3:]:
                raise ValueError(('directory/header mismatch outside mutable flags',chunk_id))
            if chunk_id in self.records:raise ValueError(('duplicate chunk ID',chunk_id))
            self.records[chunk_id]={'chunk_id':chunk_id,'directory_flags':flags,'payload_header_flags':header[2],'compression':compression,
                'compressed_bytes':compressed_bytes,'decoded_bytes':decoded_bytes,
                'file_offset':offset,'payload_offset':offset+48,'payload_stored_bytes':payload_bytes}
    def read(self,chunk_id):
        record=self.records[chunk_id];start=record['payload_offset']
        raw=bytes(self.data[start:start+record['payload_stored_bytes']])
        decoded=lz4.block.decompress(raw,uncompressed_size=record['decoded_bytes']) if record['compression'] else raw
        if len(decoded)!=record['decoded_bytes']:raise ValueError(('decoded size mismatch',chunk_id,len(decoded)))
        return decoded
    def close(self):self.data.close();self.handle.close()

def main():
    start=time.time();container=CaptureContainer();folder=OUT/'Chunks';folder.mkdir(parents=True,exist_ok=True)
    rows=[];decoded_total=0
    for chunk_id,record in sorted(container.records.items()):
        decoded=container.read(chunk_id)
        path=folder/f'chunk_{chunk_id:05d}.bin';path.write_bytes(decoded)
        rows.append({**record,'path':str(path),'sha256':hashlib.sha256(decoded).hexdigest()})
        decoded_total+=len(decoded)
        if chunk_id%5000==0:print(json.dumps({'chunk':chunk_id,'decoded_bytes':decoded_total,'elapsed_seconds':round(time.time()-start,2)}),flush=True)
    index={'capture':str(CAPTURE),'file_bytes':len(container.data),'directory_offset':container.directory_offset,
        'footer_version':container.footer_version,'chunk_count':len(rows),'decoded_total_bytes':decoded_total,
        'all_chunk_headers_match_directory_except_flags':True,'mutable_flags_note':'Directory flags0/1/2 may differ from original payload header flags; compression, byte sizes, ID and file offset must still match exactly.',
        'all_payloads_within_container':True,'all_decoded_sizes_match':True,
        'id_semantics':'Container chunk ID, not D3D12 resource UID. Resource association requires object/function-stream analysis.',
        'records':rows}
    (OUT/'chunk_index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    with (OUT/'chunk_index.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    container.close()
    print(json.dumps({'output':str(folder),'chunk_count':len(rows),'decoded_bytes':decoded_total,'elapsed_seconds':round(time.time()-start,2),'pass':True},indent=2))

if __name__=='__main__':main()
