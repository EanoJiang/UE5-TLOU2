"""Verify the final allowlist, every recorded SHA256 and all delivery evidence gates."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT/'Content/TLOU2/Reports/FINAL_DELIVERY_MANIFEST.json'
manifest_raw = manifest_path.read_bytes()
manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()
manifest = json.loads(manifest_raw)
failures = []
assert not manifest['missing_required'], manifest['missing_required']
assert not manifest['unstable_files'], manifest['unstable_files']
for item in manifest['items']:
    path = (ROOT/item['path']).resolve()
    assert path.is_relative_to(ROOT), item['path']
    if not item['exists']:
        if item['required']:
            failures.append({'path': item['path'], 'error': 'missing required file'})
        continue
    if not path.is_file():
        failures.append({'path': item['path'], 'error': 'file absent'})
        continue
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    if path.stat().st_size != item['bytes'] or digest.hexdigest() != item['sha256']:
        failures.append({'path': item['path'], 'error': 'size or SHA256 mismatch'})
failed_states = [key for key, value in manifest['validation'].items() if value is not True]
manifest_stable = hashlib.sha256(manifest_path.read_bytes()).hexdigest() == manifest_sha256
report = {'manifest': str(manifest_path), 'manifest_sha256': manifest_sha256,
          'manifest_unchanged_during_audit': manifest_stable,
          'verified_files': sum(bool(item['exists']) for item in manifest['items']),
          'verified_bytes': sum(item.get('bytes',0) for item in manifest['items'] if item['exists']),
          'failed_validation_states': failed_states, 'file_failures': failures,
          'pass': not failures and not failed_states and manifest_stable,
          'scope': 'Artifact integrity and declared evidence gates. Material optical equivalence and unrecovered source helper transforms remain documented limits; passing does not erase those limits.'}
(ROOT/'Exports/final_delivery_integrity_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
assert report['pass'], 'Final delivery integrity or evidence gates failed'
