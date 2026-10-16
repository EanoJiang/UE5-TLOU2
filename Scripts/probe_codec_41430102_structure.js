const fs = require('fs');
const crypto = require('crypto');
const src = 'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak';
const b = fs.readFileSync(src);
const page = 9541328, codec = 9809440, payload = 2496;
const out = 'D:/TLOU2_UE5_8_Codex/Content/TLOU2/Reports';
const u16 = o => b.readUInt16LE(o);
const u32 = o => b.readUInt32LE(o);
const f32 = o => b.readFloatLE(o);
const hx = x => '0x' + x.toString(16);
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const h = {
  magic: hx(u32(codec)), hash_word: hx(u32(codec + 4)), payload_size: u16(codec + 8),
  groups: u16(codec + 12), frames: u16(codec + 14), legacy_field_14: hx(u32(codec + 0x14)),
  legacy_field_18: hx(u32(codec + 0x18)), default_rate: f32(codec + 0x1c),
  frame_count_alt: u16(codec + 0x22), sample_period: f32(codec + 0x2c),
  section_table_offset: hx(u32(codec + 0x30)), section_table_flags: hx(u32(codec + 0x34)),
  frame_stream_start: hx(u32(codec + 0x38)), frame_stride_packed: hx(u32(codec + 0x3c)),
  channel_table_offset: hx(u32(codec + 0x40)), external_flags_or_size: hx(u32(codec + 0x44)),
  frame_stream_end: hx(u32(codec + 0x48))
};
const recs = [];
for (let o = 0x50; o < 0xa0; o += 0x10) recs.push({
  header_offset: hx(o), field0: hx(u32(codec + o)), field1: u32(codec + o + 4),
  field2: hx(u32(codec + o + 8)), field3: hx(u32(codec + o + 12))
});
const groups = [];
for (let o = 0x120; o < 0x160; o += 8) groups.push({ offset: hx(o), u16: [u16(codec + o), u16(codec + o + 2), u16(codec + o + 4), u16(codec + o + 6)] });
const words = [];
for (let o = 0x160; o < 0x1f0; o += 2) words.push({ offset: hx(o), u16: u16(codec + o) });
const regions = [];
for (const a of [0, 0x50, 0x120, 0x160, 0x1f0, 0x210, 0x2a0, 0x2b0, 0x390, 0x500, 0x9b0]) {
  const x = b.subarray(codec + a, Math.min(codec + payload, codec + a + 0x20));
  regions.push({ offset: hx(a), sha256: sha(x), bytes: x.toString('hex') });
}
const observations = [
  'Header bytes 0x00..0x4f are mixed-width; +0x08 is payload byte count 2496, +0x0c groups 7, +0x0e frames 80, +0x1c rate 30 Hz, +0x2c period 1/30 s.',
  '+0x30 is a section/table offset (0x120) and +0x34 is a flags word; they are not a verified descriptor count. +0x38=0x500, +0x40=0x2a0, +0x48=0x9b0 are payload-relative landmarks also seen across neighboring movement clips.',
  'Five 16-byte records at +0x50..+0x9f have first fields 0x2b0,0x4c0,0x4d0,0x4e0,0x4f0 and a shared end pointer 0x9b0; this is a section index/table. Their second fields vary with frame count (0x26,0x60,0x63,0x5e,0x32).',
  'Payload-relative tables at +0x120 and +0x160 are stable across 80/92-frame neighboring clips; only small frame-dependent counters and bytes from about +0x210 onward change. This supports metadata/quantization table versus compressed sample stream.',
  'Bytes at +0x210..+0x9af are high-entropy stream blocks bounded by section landmarks; no bone hash or channel ID is recoverable from this header alone.',
  'The header does not independently expose a descriptor count at +0x30; descriptor records/semantics and channel-to-bone mapping remain unresolved; no decoded animation claim is made.'
];
const report = { source: src, source_size: b.length, page_index: 9, page_offset: page, codec_absolute_offset: codec, codec_page_relative: codec - page, payload_range: [codec, codec + payload], payload_sha256: sha(b.subarray(codec, codec + payload)), header: h, header_section_records: recs, group_table_u16: groups, constant_table_u16: words, region_samples: regions, observations };
fs.writeFileSync(out + '/CODEC_41430102_STRUCTURE_TARGET.json', JSON.stringify(report, null, 2));
const md = ['# 0x41430102 structure probe — ellie-prone-lg-aim-strafe-0-fw', '', 'Source: ' + src, '', 'Codec header absolute offset: ' + codec + ' (page 9 relative ' + hx(codec - page) + ')', 'Payload: ' + payload + ' bytes, SHA-256 ' + report.payload_sha256, '', '## Verified mixed-width header', '', '| field | value |', '|---|---:|'];
for (const [k, v] of Object.entries(h)) md.push('| ' + k + ' | ' + v + ' |');
md.push('', '## Section index at +0x50', '', '| rel | field0 | field1 | field2 | field3 |', '|---:|---:|---:|---:|---:|');
for (const r of recs) md.push('| ' + r.header_offset + ' | ' + r.field0 + ' | ' + r.field1 + ' | ' + r.field2 + ' | ' + r.field3 + ' |');
md.push('', '## Group table words (+0x120)', '', '| rel | u16[0] | u16[1] | u16[2] | u16[3] |', '|---:|---:|---:|---:|---:|');
for (const g of groups) md.push('| ' + g.offset + ' | ' + g.u16.map(x => hx(x)).join(' | ') + ' |');
md.push('', '## Evidence interpretation', '', ...observations.map(x => '- ' + x), '', 'This probe stops at structural evidence. It does **not** decode proprietary quantized channels, map descriptors to bones, or produce a UE-valid original animation.');
fs.writeFileSync(out + '/CODEC_41430102_STRUCTURE_TARGET.md', md.join('\n') + '\n');
console.log(JSON.stringify({ json: out + '/CODEC_41430102_STRUCTURE_TARGET.json', md: out + '/CODEC_41430102_STRUCTURE_TARGET.md', payload_sha256: report.payload_sha256 }, null, 2));




