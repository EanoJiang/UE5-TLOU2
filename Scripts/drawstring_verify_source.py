"""Independent acceptance gate for the omitted source drawstring asset."""
import hashlib
import json
from pathlib import Path
import numpy as np

OUT = Path('D:/TLOU2_UE5_8_Codex/Exports/Drawstring')

def main():
    assert (OUT/'capture.json').exists(), 'Drawstring capture is not exported yet'
    doc = json.loads((OUT/'capture.json').read_text())
    rig = json.loads((OUT/'owned_rig22.json').read_text())
    assert rig['bone_count'] == rig['original_sqt_count'] == 22
    mesh = next(m for m in doc['meshes'] if '_LODShape0_' in m['name'])
    assert mesh['vertex_count'] == 441 and mesh['count'] == 2208
    z = np.load(OUT/mesh['npz'])
    ix = z['indices_raw'].view('<u2')[:mesh['count']]
    assert len(ix) == 2208 and int(ix.min()) == 0 and int(ix.max()) == 440
    n = mesh['vertex_count']
    idt = '<u2' if mesh['bindings']['bidx']['type'] == 4 else '<u4'
    wdt = '<f4' if mesh['bindings']['bwgt']['type'] == 0 else '<u4'
    ids = z['bidx_raw'].view(idt)[:n*12].reshape(n,12)
    vals = z['bwgt_raw'].view(wdt)[:n*12].reshape(n,12)
    assert np.isfinite(vals).all() and (vals >= 0).all() and (vals.sum(1) > 0).all()
    assert int(ids[vals > 0].max()) < 22
    report = dict(pass_=True, vertices=n, triangles=len(ix)//3, rig_bones=22,
        indices_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),
        source_weight_dtype=wdt, source_weight_sum_min=float(vals.sum(1).min()),
        source_weight_sum_max=float(vals.sum(1).max()),
        source_positive_influences_max=int((vals>0).sum(1).max()),
        source_positive_bone_indices=sorted(int(x) for x in np.unique(ids[vals>0])),
        source_positive_influences=int((vals>0).sum()),
        uv_channels=[k for k in mesh['bindings'] if k.startswith('uv')])
    report['pass'] = report.pop('pass_')
    (OUT/'source_verification.json').write_text(json.dumps(report,indent=2))
    print('DRAWSTRING_SOURCE_VERIFY '+json.dumps(report))

if __name__ == '__main__': main()
