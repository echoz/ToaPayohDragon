"""Attach checked, hash-matched offline slicing evidence to the v03 manifest."""
from pathlib import Path
import collections, hashlib, json, re, shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/dragon-pla-kit-v03'
WORK=OUT/'work/slicer'
m=json.loads((OUT/'manifest.json').read_text())
results=json.loads((WORK/'slicing-report.json').read_text())
assert len(results)==len(m['plates'])
expected={p['file']:p for p in m['plates']}
rows=[];grams=collections.defaultdict(float);seconds=0
for r in results:
    path=ROOT/r['input'];rel=str(path.relative_to(OUT));p=expected.pop(rel)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
    assert r['passed'] and r['returncode']==0
    assert bool(p['supports_required'])==bool(r['supports_enabled'])
    assert not p['supports_required'] or r['support_toolpaths_generated']
    g=r['gcode'];comments='\n'.join(x for s in g for x in s['summary_comments'])
    mass=sum(float(x) for x in re.findall(r'total filament weight \[g\]\s*:\s*([\d.]+)',comments))
    times=re.findall(r'total estimated time:\s*([^\n;]+)',comments)
    sec=sum(int(v)*{'h':3600,'m':60,'s':1}[unit] for t in times for v,unit in re.findall(r'(\d+)([hms])',t))
    assert mass>0 and sec>0
    grams[p['color']]+=mass;seconds+=sec
    evidence=WORK/(path.parent.name+'_'+path.stem)/'result.json'
    rows.append(dict(plate=p['name'],input=rel,sha256=r['sha256'],passed=True,returncode=0,
        layer_count=sum(s['layer_changes'] for s in g),extrusion_moves=sum(s['extrusion_moves'] for s in g),
        support_extrusion_moves=sum(s['support_extrusion_moves'] for s in g),supports_enabled=r['supports_enabled'],
        brim_width_mm=r['brim_width_mm'],estimated_pla_g=round(mass,2),estimated_time=' + '.join(times),
        estimated_time_seconds=sec,evidence=str(evidence.relative_to(OUT))))
assert not expected
status=f'passed_all_{len(rows)}_plates'
v=dict(engine='Bambu Studio 02.08.02.61',status=status,plate_count=len(rows),
    production_plates=sum(not p['test'] for p in m['plates']),test_plates=sum(p['test'] for p in m['plates']),
    plate='Textured PEI Plate (assumed)',printer='Bambu Lab X1 Carbon 0.4 nozzle',filament='Generic PLA',
    process='0.16mm High Quality @BBL X1C',overrides=dict(wall_loops=3,sparse_infill_density='15%',
        support_type='tree(auto), build plate only on supported plates',brim_mm='3; 5 on cream supported plate with head platform'),
    estimated_pla_total_g=round(sum(grams.values()),2),estimated_pla_by_color_g={c:round(w,2) for c,w in grams.items()},
    estimated_total_time_seconds=seconds,estimated_total_time=f'{seconds//3600}h {(seconds%3600)//60}m {seconds%60}s',
    physical_test='Not performed; coupon and actual dry fit still required.',printer_sent=False,
    gcode_policy='Temporary validation G-code inspected then removed. Import STLs using actual plate and calibrated PLA.',plates=rows)
m['validation']['slicer_status']=status
m['validation']['cantilever_review']='Actual STL layer screening in validation/print-v03-audit.json. Supported parts require careful removal and physical dry fitting; see CANTILEVER-REVIEW.md.'
m['validation']['tail_audit']='validation/tail-v03-print-audit.json'
m['slicer_validation']=v
(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
(OUT/'validation').mkdir(exist_ok=True)
for file in ['resolved-machine.json','resolved-process.json','resolved-filament.json','profile-assumptions.json']:
    shutil.copy2(WORK/file,OUT/'validation'/file)
(OUT/'validation/validation-summary.json').write_text(json.dumps(v,indent=2))
print(json.dumps({k:v[k] for k in ['status','estimated_pla_total_g','estimated_total_time']}))
