"""Gate a release on recorded digital checks and summarize the actual fixes."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/dragon-pla-kit-v03'
m=json.loads((OUT/'manifest.json').read_text())
checks={'export-v03-audit.json':('status','passed'),'body-v03-fit-audit.json':('passed',True),'head-v03-fit-audit.json':('status','passed'),'entrance-v03-fit-audit.json':('status','PASS'),'base-slides-v03-fit-audit.json':('passed',True),'aids-v03-fit-audit.json':('status','PASS')}
for filename,(key,value) in checks.items():
 r=json.loads((OUT/'validation'/filename).read_text());assert r[key]==value,(filename,r.get('failures'))
mesh=json.loads((OUT/'validation/export-v03-audit.json').read_text())
for p in mesh['parts']:assert hashlib.sha256((OUT/p['file']).read_bytes()).hexdigest()==p['sha256'],p['name']
print_audit=json.loads((OUT/'validation/print-v03-audit.json').read_text())
assert not print_audit['unresolved_support_free_parts']
for p in print_audit['parts']:assert hashlib.sha256((OUT/p['file']).read_bytes()).hexdigest()==p['sha256'],p['part']
assert m['validation']['slicer_status']==f'passed_all_{len(m["plates"])}_plates'
m['status']='v03 digital mesh, fit, seating, insertion, layer and slicer checks passed. Physical PLA fit untested; print representative samples before the complete model.'
m['validation']['tolerance_audit']='passed_digital_v03_physical_samples_pending'
m['validation']['fit_reports']=list(checks)
m['validation']['all_file_hashes_verified']=True
m['validation']['physical_test']='pending'
(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
for source in ['body-v03-fit-review.md','head-v03-fit-review.md','entrance-v03-fit-review.md','base-slides-v03-fit-review.md','aids-v03-review.md']:
 p=ROOT/'docs'/source
 if p.exists():
  doc=p.read_text().replace('../exports/dragon-pla-kit-v03/','')
  doc=re.sub(r'\[([^\]]+)\]\((work/[^)]+)\)',r'`\1` (workspace-only evidence)',doc)
  (OUT/source).write_text(doc)
text='''# v03 tolerance corrections — digitally passed, physical fit pending

The v02 findings have been addressed in the new v03 geometry. The approved silhouette is retained; changes principally affect hidden sockets, shoulders, insertion corridors, glue recesses and assembly aids. Archived v02 remains unchanged. Use matching v03 parts only.

| Audited issue | Correction and check |
|---|---|
| Head platform hit eye rims during installation | Complete top-drop corridor cleared; inward-open shelf receivers print without bridged crowns. Actual-STL top-drop and first-hoop paths pass. |
| Rung18 landing had zero side margin | 0.20 mm side allowance, entry relief and preserved Z0.70 bearing datum. Both axes/diagonals checked. |
| Tight curved rail seats and difficult entry | Seats cut from actual curved rails and swept along installation directions. Minimum tested directional margin about 0.215 mm; all section paths pass. |
| Rails met with only 0.05 mm end gaps | All twelve joins now have 0.25 mm gaps. |
| Hoops floated and tilted; beams could sit low | Wider keys, two positive shoulders and 1.20 mm socket floors. Flat beam blocks meet pier pads. Actual height/tilt/contact probes pass. |
| Pins barely reached structural tray; sand could block feet | Whole head/pier/tail keys reach 4.2 mm below ground, slide loose keys do likewise. Approximately 2.2 mm tray engagement; head lead-in leaves about 1.75 mm straight locating engagement. Sand has larger passages and round-plus-slot registration. |
| Split pins and unregistered glue halves | Mechanical keys belong to one lamination, sharing its print plane. Nine full-outline, open-centre cradles guide matching bare halves; placement, removal and registration checked. |
| Colour inserts lacked a reliable face-height datum | Bearing lands stop inserts; surrounding 0.20 mm recess accepts glue. Positive seating and approach paths checked. |
| Handrail pins depended on blue insert alignment | Cream sockets locate pins; larger blue apertures clear them. Collars rest on cream pads, setting 0.40 mm stand-off; second socket floats along the pitch. |
| Ladder required a tiny slide-and-lift manoeuvre | Direct horizontal insertion at final height. Nominal gap 0.30 mm; sampled motion gives a conservative continuous lower bound of about 0.27 mm. |
| Slide2 left insert snagged during insertion | Complete approach sweep relieved; actual insert facets establish curved bearing lands. All four insert approach paths pass. |
| Base join pockets bridged, seam height/spacing floated | Pockets open from the top; close butt faces before inserting loose keys. Sand bears on rims/pads above glue relief. |
| Nominal coupon did not reproduce supported joints | 29 samples include actual curved rails, beam seats/join, supported platform peg, whole feet through tray/sand, handrail/colour insert, landing, ladder and full reusable slide2 shell/insert. |

## Evidence and limits

The global audit restores every delivered STL to assembly coordinates using its recorded print transform, verifies topology and hashes, and checks all production part pairs. Reported overlap threshold is 0.015 mm³ to exclude tiny triangulation/contact artifacts; more stringent local checks are used in individual fit reports. Actual meshes are used for body, head, entrance, base/slide and cradle verification. All supported plates produce actual support extrusion in offline Bambu Studio slicing.

The overhang screen samples layers at 0.16 mm spacing, starts 0.10 mm above the bed and reports growth/new islands above 0.02 mm². Face-angle comparisons allow 0.01° numerical tolerance: a few mathematically 45° tray chamfer facets move about 0.001° past the threshold after float32 rounding. Raw metrics remain in the report. No piece declared support-free has an unresolved material flag.

These are geometry and slicer checks. They do not measure filament variation, actual first-layer spread, support-removal damage, surface roughness, adhesion or glue/clamp behaviour. Small finite-clearance joints and cradles intentionally permit some movement before gluing. A guide is not a press-fit clamp. Print the representative samples at the production settings, verify stable full seating with light finger pressure, then dry-fit the complete model before gluing.

## Recorded reports

- [Global delivered-STL audit](validation/export-v03-audit.json)
- [Body and curved rails](validation/body-v03-fit-audit.json)
- [Head platform and feet](validation/head-v03-fit-audit.json)
- [Tail and ladder](validation/entrance-v03-fit-audit.json)
- [Base, piers and slides](validation/base-slides-v03-fit-audit.json)
- [Assembly cradles and base samples](validation/aids-v03-fit-audit.json)
- [All-part print screen](validation/print-v03-audit.json)
- [Offline slicer evidence](validation/validation-summary.json)

Start with [FIT-TESTS.md](FIT-TESTS.md). The fit tests must pass physically before committing to the complete production batch.
'''
(OUT/'TOLERANCE-REVIEW.md').write_text(text)
(ROOT/'docs/tolerance-corrections-v03.md').write_text(text.replace('](validation/','](../exports/dragon-pla-kit-v03/validation/').replace('](FIT-TESTS.md)','](../exports/dragon-pla-kit-v03/FIT-TESTS.md)'))
print('All v03 digital release gates passed')
