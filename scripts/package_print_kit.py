"""Package validated STLs, maps and readable evidence; omit build scratch."""
from pathlib import Path
import json,zipfile,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/dragon-pla-kit-v03'
m=json.loads((OUT/'manifest.json').read_text())
assert m['validation']['slicer_status']==f'passed_all_{len(m["plates"])}_plates'
assert not m['inter_part_overlaps']
assert m['validation']['tolerance_audit']=='passed_digital_v03_physical_samples_pending'
assert (OUT/'README.md').is_file()
assert (OUT/'FIT-TESTS.md').is_file()
assert (OUT/'preview/opposite.png').is_file()
assert (OUT/'validation/tail-v03-print-audit.json').is_file()
v=m['slicer_validation']
for p in v['plates']:
 src=OUT/'work/slicer'/Path(p['evidence']).parent.name
 dest=OUT/'validation'/src.name;dest.mkdir(exist_ok=True)
 for f in src.iterdir():
  if f.suffix in {'.json','.log'}:shutil.copy2(f,dest/f.name)
 p['evidence']=str((dest/'result.json').relative_to(OUT))
 assert (OUT/p['evidence']).is_file()
 assert hashlib.sha256((OUT/p['input']).read_bytes()).hexdigest()==p['sha256']
(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
(OUT/'validation/validation-summary.json').write_text(json.dumps(v,indent=2))
audit_path=OUT/'validation/tail-v03-print-audit.json'
audit=json.loads(audit_path.read_text())
assert not audit['unresolved_support_free_parts']
for record in audit['parts']:
 assert hashlib.sha256((OUT/record['file']).read_bytes()).hexdigest()==record['sha256']
if 'manifest_sha256' in audit:
 audit['manifest_sha256_at_audit']=audit.pop('manifest_sha256')
audit['manifest']='manifest.json'
audit['manifest_note']='Audit used the geometry export manifest before slicing metadata was appended. Individual STL hashes were rechecked during packaging; SHA256SUMS.txt covers the final manifest.'
audit_path.write_text(json.dumps(audit,indent=2))
files=sorted(p for p in OUT.rglob('*') if p.is_file() and 'work' not in p.relative_to(OUT).parts and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT))+'\n' for p in files))
files.append(OUT/'SHA256SUMS.txt')
zip_path=ROOT/'exports/dragon-pla-kit-v03.zip'
stl_count=len(m['parts'])+len(m['plates'])
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:z.write(p,Path('dragon-pla-kit-v03')/p.relative_to(OUT))
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert sum(n.endswith('.stl') for n in z.namelist())==stl_count
 assert not any('/work/' in n for n in z.namelist())
print(json.dumps({'zip':str(zip_path),'bytes':zip_path.stat().st_size,'stls':stl_count,'production_parts':m['part_count'],'tests':m['test_part_count'],'plate_layouts':m['plate_count'],'files':len(files)}))
