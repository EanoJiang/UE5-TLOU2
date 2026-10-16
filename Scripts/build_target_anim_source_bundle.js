// Build a stable, reviewable source bundle for the named Ellie movement clip.
// This copies the exact codec payload bytes already extracted by the container
// reader and records the source PAK offsets, hashes, and unresolved semantics.
const fs = require('fs');
const crypto = require('crypto');

const root = 'D:/TLOU2_UE5_8_Codex';
const sourcePak = 'D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak';
const rawDir = `${root}/Exports/AnimationSources/raw/anim-ellie-player-movement`;
const outDir = `${root}/Exports/AnimationSources/DecodedRawChannels/codec_evidence`;
const reportDir = `${root}/Content/TLOU2/Reports`;
const source = fs.readFileSync(sourcePak);
const sha256 = data => crypto.createHash('sha256').update(data).digest('hex');

const clips = [
  {
    name: 'ellie-prone-lg-aim-strafe-0-fw',
    animEntry: 468,
    animAbsoluteOffset: 10309744,
    codecAbsoluteOffset: 9809440,
    codecPageRelativeOffset: 0x41750,
    payloadBytes: 2496,
    rawCodecFile: `${rawDir}/codec_495.ndanim.bin`,
    output: `${outDir}/ellie-prone-lg-aim-strafe-0-fw_41430102_payload.ndanim.bin`,
    frameCount: 80,
    frameRate: 30,
    groupCount: 7,
    sectionOffset: 0x120,
    descriptorCount: null,
    externalPointerPageRelative: 0x8e150,
    externalJointRegion: { start: 0x8e9e8, end: 0x8ed98, recordStride: 48, parsedRecords: 20 }
  },
  {
    name: 'ellie-prone-lg-aim-strafe-0-fw-crossbow',
    animEntry: 652,
    animAbsoluteOffset: 10332384,
    codecAbsoluteOffset: 9814432,
    codecPageRelativeOffset: 0x429c0,
    payloadBytes: 2496,
    rawCodecFile: `${rawDir}/codec_497.ndanim.bin`,
    output: `${outDir}/ellie-prone-lg-aim-strafe-0-fw-crossbow_41430102_payload.ndanim.bin`,
    frameCount: 80,
    frameRate: 30,
    groupCount: 7,
    sectionOffset: 0x120,
    descriptorCount: null,
    externalPointerPageRelative: 0x8e150,
    externalJointRegion: { start: 0x8e9e8, end: 0x8ed98, recordStride: 48, parsedRecords: 20 }
  }
];

for (const clip of clips) {
  const raw = fs.readFileSync(clip.rawCodecFile);
  if (raw.length < clip.payloadBytes || raw.readUInt32LE(0) !== 0x41430102) {
    throw new Error(`${clip.name}: extracted codec resource is shorter than the payload or has a bad magic`);
  }
  const payload = source.subarray(clip.codecAbsoluteOffset, clip.codecAbsoluteOffset + clip.payloadBytes);
  // The raw reader preserves a larger resource span. Keep the exact codec
  // payload as a stable standalone artifact and validate the first bytes.
  if (payload.readUInt32LE(0) !== 0x41430102) throw new Error(`${clip.name}: codec magic mismatch`);
  fs.writeFileSync(clip.output, payload);
  clip.payloadSha256 = sha256(payload);
  clip.sourcePakSha256 = sha256(source);
  clip.standalonePayloadBytes = payload.length;
  clip.magic = '0x41430102';
  clip.status = 'byte_preserved_codec_payload';
}

const bundle = {
  tool: 'build_target_anim_source_bundle.js',
  version: 1,
  sourcePak,
  sourcePakSha256: sha256(source),
  page9Offset: 9541328,
  clips,
  semantics: {
    verified: ['container offsets', 'codec magic', 'payload size', 'frame count', '30 Hz header clock', 'group count', 'section/table offset 0x120', 'external pointer and joint region boundary'],
    unresolved: ['codec descriptor to skeleton bone mapping', 'frame/channel ordering', 'quantizer bit layout', 'interpolation/delta rules', 'transform units', 'game-space root-motion meaning'],
    ueAssetPolicy: 'The UE AnimSequence and GIF remain explicitly labeled interchange probes; these standalone files are the original compressed payload evidence.'
  }
};

fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(reportDir, { recursive: true });
fs.writeFileSync(`${reportDir}/TARGET_ANIM_SOURCE_BUNDLE.json`, JSON.stringify(bundle, null, 2));
const lines = [
  '# Target Ellie movement codec source bundle',
  '',
  'This bundle preserves the exact `0x41430102` codec payloads for the named clip and its crossbow variant. The payload bytes are extracted directly from `anim-ellie-player-movement.pak`; no proprietary transform semantics are inferred.',
  '',
  '| Clip | ANIM entry | Codec offset | Frames | Bytes | Payload SHA-256 |',
  '|---|---:|---:|---:|---:|---|'
];
for (const c of clips) lines.push(`| \`${c.name}\` | ${c.animEntry} | ${c.codecAbsoluteOffset} | ${c.frameCount} @ ${c.frameRate} Hz | ${c.standalonePayloadBytes} | \`${c.payloadSha256}\` |`);
lines.push('', '## Verified source facts', '', '- Both payloads begin with codec magic `0x41430102`.', '- The primary clip is ANIM entry 468 at absolute offset 10,309,744; its codec begins at 9,809,440 and has 2,496 bytes.', '- The primary header reports 80 frames, 30 Hz, 7 groups, and a section/table offset of `0x120` at `+0x30`; a descriptor count of 288 is not independently established.', '- The primary external pointer resolves to page 9 relative `0x8e150`; the joint-record region is preserved separately in the JSON report.', '', '## Unresolved semantics', '', ...bundle.semantics.unresolved.map(x => `- ${x}`), '', 'The UE animation and GIF are interchange probes backed by this source evidence. They are not relabeled as original game animation until these semantics are decoded and validated.');
fs.writeFileSync(`${reportDir}/TARGET_ANIM_SOURCE_BUNDLE.md`, lines.join('\n') + '\n');
console.log(JSON.stringify({ report: `${reportDir}/TARGET_ANIM_SOURCE_BUNDLE.json`, payloads: clips.map(c => ({ name: c.name, bytes: c.standalonePayloadBytes, sha256: c.payloadSha256 })) }, null, 2));
