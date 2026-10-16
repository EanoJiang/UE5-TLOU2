"""Read the game's DSAR/PSARC archives without materializing the whole archive.

DSAR container and PSARC records follow the local UnPSARC_stream2 source.
Only requested blocks are decompressed; this is useful for named pose assets.
"""
import argparse
import bisect
import functools
import hashlib
import json
from pathlib import Path
import struct
import zlib
import lz4.block


class RandomDSAR:
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open('rb')
        head = self.file.read(32)
        self.ds = head[:4] == b'DSAR'
        self.blocks = []
        if self.ds:
            count = struct.unpack_from('<I', head, 8)[0]
            raw = self.file.read(count * 32)
            for i in range(count):
                self.blocks.append(struct.unpack_from('<QQIIB7x', raw, 32*i))
            self.starts = [b[0] for b in self.blocks]

    @functools.lru_cache(maxsize=64)
    def block(self, i):
        offset, compressed_offset, size, compressed_size, codec = self.blocks[i]
        if not compressed_size:
            return bytes(size)
        self.file.seek(compressed_offset)
        raw = self.file.read(compressed_size)
        if codec == 0:
            result = raw
        else:
            result = lz4.block.decompress(raw, uncompressed_size=size)
        if len(result) != size:
            raise ValueError((i, len(result), size))
        return result

    def read(self, offset, size):
        if not self.ds:
            self.file.seek(offset)
            return self.file.read(size)
        out = bytearray()
        while len(out) < size:
            i = bisect.bisect_right(self.starts, offset) - 1
            b = self.block(i)
            local = offset - self.starts[i]
            n = min(len(b)-local, size-len(out))
            if n <= 0:
                raise ValueError(('DSAR gap', offset, size))
            out += b[local:local+n]
            offset += n
        return bytes(out)


class Archive:
    def __init__(self, path):
        self.source = RandomDSAR(path)
        head = self.source.read(0, 32)
        if head[:4] != b'PSAR':
            raise ValueError(head.hex())
        self.compression = head[8:12]
        data_start, stride, count, self.block_size, flags = struct.unpack_from('>5I', head, 12)
        table = self.source.read(32, data_start-32)
        self.entries = []
        for i in range(count):
            b = table[i*stride:(i+1)*stride]
            self.entries.append(dict(index=i, hash=b[:16].hex(), block=struct.unpack_from('>I', b, 16)[0],
                                     size=int.from_bytes(b[20:25], 'big'), offset=int.from_bytes(b[25:30], 'big')))
        raw_sizes = table[stride*count:]
        self.sizes = [int.from_bytes(raw_sizes[i:i+2], 'big') for i in range(0,len(raw_sizes)-1,2)]
        names = self.extract(self.entries[0]).decode('utf8').replace('\0','\n').splitlines()
        mapping = {}
        for name in names:
            for variant in (name, name.lower(), name.upper()):
                mapping[hashlib.md5(variant.encode('ascii')).hexdigest()] = name
        for e in self.entries:
            e['name'] = mapping.get(e['hash'])

    def extract(self, e):
        remaining = e['size']
        offset = e['offset']
        index = e['block']
        out = bytearray()
        while remaining > 0:
            compressed = self.sizes[index] or self.block_size
            size = min(self.block_size, remaining)
            raw = self.source.read(offset, compressed)
            if self.compression == b'zlib' and raw[:2] == b'\x78\xda':
                raw = zlib.decompress(raw)
            elif self.compression == b'oodl' and raw[:2] == b'\x8c\x06':
                raise NotImplementedError('Oodle inner block; use game DLL')
            if len(raw) != size:
                raise ValueError(('PSARC block length', e, index, len(raw), size))
            out += raw
            remaining -= size
            offset += compressed
            index += 1
        return bytes(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('archive')
    p.add_argument('--pattern', default='')
    p.add_argument('--out')
    p.add_argument('--list-json')
    a = p.parse_args()
    archive = Archive(a.archive)
    matches = [e for e in archive.entries[1:] if a.pattern.lower() in (e['name'] or '').lower()]
    print(json.dumps(dict(archive=a.archive, count=len(archive.entries), compression=archive.compression.decode(),
                          matches=matches), ensure_ascii=False, indent=2))
    if a.list_json:
        Path(a.list_json).write_text(json.dumps(archive.entries, indent=2), encoding='utf8')
    if a.out:
        output = Path(a.out).resolve()
        output.mkdir(parents=True, exist_ok=True)
        for e in matches:
            target = (output / e['name'].lstrip('/')).resolve()
            if output not in target.parents:
                raise ValueError(('unsafe archive path', target))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extract(e))
            print('EXTRACTED', target, target.stat().st_size)


if __name__ == '__main__':
    main()
