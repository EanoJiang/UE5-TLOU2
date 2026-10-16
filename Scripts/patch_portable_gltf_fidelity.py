"""Configure the task's dedicated portable exporter for source-preserving export.

Stock Blender glTF validates away duplicate polygons and filters weights<=1e-4.
Both are inappropriate for preserving the captured source data. Original addon
files are backed up; only this task's portable Blender installation is patched.
"""
import hashlib
import json
import argparse
from pathlib import Path

ROOT=Path('D:/TLOU2_UE5_8_Codex')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--addon',type=Path,default=Path('D:/Unpack_3A/blender_portable/blender-4.5.10-windows-x64/4.5/scripts/addons_core/io_scene_gltf2/blender/exp'))
parser.add_argument('--backup-name',default='OriginalBlenderGLTF')
parser.add_argument('--report-name',default='portable_gltf_fidelity_exporter.json')
args=parser.parse_args()
ADDON=args.addon.resolve()
assert ADDON.is_relative_to(Path('D:/Unpack_3A/blender_portable')), 'Patch only task-isolated portable Blender installations'
assert Path(args.backup_name).name==args.backup_name and Path(args.report_name).name==args.report_name
BACKUP=ROOT/'Scripts/ExporterSupport'/args.backup_name
BACKUP.mkdir(parents=True,exist_ok=True)
changes=[('nodes.py','res = blender_object.data.validate()',
          'res = False  # TLOU2 fidelity: prevalidated source duplicate triangles must survive'),
         ('primitive_extract.py','min_influence = 0.0001',
          'min_influence = 0.0  # TLOU2 fidelity: retain every original positive influence')]
rows=[]
for filename,old,new in changes:
    path=ADDON/filename
    original=path.read_bytes()
    text=original.decode('utf-8')
    backup=BACKUP/filename
    if new in text:
        assert backup.exists(), 'Original exporter backup required'
        before=backup.read_bytes()
    else:
        assert text.count(old)==1,(filename,'unexpected exporter version')
        if backup.exists(): assert backup.read_bytes()==original, 'Exporter changed since backup'
        else: backup.write_bytes(original)
        before=original
        path.write_bytes(text.replace(old,new).encode('utf-8'))
    after=path.read_bytes()
    assert after.decode('utf-8').count(new)==1
    compile(after,str(path),'exec')
    rows.append({'file':str(path),'backup':str(backup),'original_sha256':hashlib.sha256(before).hexdigest(),
                 'patched_sha256':hashlib.sha256(after).hexdigest(),'old_statement':old,'new_statement':new})
(ROOT/'Exports'/args.report_name).write_text(json.dumps({'pass':True,'changes':rows,
    'precondition':'Source vertices, weights, triangle indices and finite transforms are independently validated before export.'},indent=2))
print('PORTABLE_GLTF_FIDELITY_PATCHED '+str(len(rows)))
