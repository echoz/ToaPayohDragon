"""Write the release guide from the final manifest and validation results."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'exports/dragon-pla-kit-v03'
m=json.loads((OUT/'manifest.json').read_text());v=m['slicer_validation']
prod=[p for p in m['parts']if not p['test']];fit=[p for p in m['parts']if p['test']and p['tags'].get('purpose')!='assembly_jig'];aids=[p for p in m['parts']if p['tags'].get('purpose')=='assembly_jig']
supported=[p for p in prod if p['supports']!='none'];flat=[p for p in prod if p['supports']=='none']
production_plates=sum(p['purpose']=='production'for p in m['plates']);fit_plates=sum(p['purpose']=='fit_test'for p in m['plates']);jig_plates=sum(p['purpose']=='assembly_jig'for p in m['plates'])
rows=[]
for purpose,label in [('production','Model'),('fit_test','Fit samples'),('assembly_jig','Optional assembly cradles')]:
 names={p['name']for p in m['plates']if p['purpose']==purpose};r=[p for p in v['plates']if p['plate']in names]
 seconds=sum(x['estimated_time_seconds']for x in r);grams=sum(x['estimated_pla_g']for x in r)
 rows.append(f'| {label} | {len(r)} | {grams:.1f} g | {seconds//3600} h {(seconds%3600)//60} min |')
text=f'''# Dragon Playground PLA print kit — v03

The tolerance revision keeps the approved cute silhouette and corrects hidden fits, seating surfaces and assembly access. Prepared for **Bambu Lab X1 Carbon, 0.4 mm nozzle, PLA**, with separate colour STLs and glue assembly. No AMS required.

**Use only matching v03 parts.** Body keys, rail seats, head platform, feet, sand, tray and tail joints changed together. Do not mix with v01/v02. Those exports remain archived.

**Digital checks passed; physical printing and fit are still untested. Print the real joint samples first.** All {len(m['plates'])} packed plates generated valid offline Bambu Studio toolpaths. All {len(m['parts'])} individual STLs are watertight, positive-volume single solids. Actual-STL clearance, insertion, seating and overhang evidence is in `validation/` and [TOLERANCE-REVIEW.md](TOLERANCE-REVIEW.md). The kit contains {len(prod)} model parts, {len(fit)} fit samples and {len(aids)} optional alignment cradles.

[Fit tests — start here](FIT-TESTS.md) · [Numbered plate/assembly map](assembly-map.html) · [Assembled preview](preview/opposite.png) · [Support review](CANTILEVER-REVIEW.md)

## Files and colour

`parts/<colour>/` contains individual model STLs. `test-first/<colour>/` contains fit samples and `test_jig_*` cradles. `plates/<colour>/` contains the same parts in convenient layouts: `plate_*` = model; `test_*` = fit samples; `jig_*` = optional assembly aids. Print either individual files or their plate, not both. Keep filenames/labels with the loose parts.

Six colours: warm ivory cream, terracotta orange, muted medium blue, soft sage green, brick red, sandy beige. The body test pieces use blue for convenience; repeat critical fits with the production PLA if colours/material batches behave differently.

**Millimetres, 100% scale, supplied orientations.** Individual STLs sit on Z=0 in printing position; they are not assembly-position files. Packed STLs contain several pieces; `assembly-map.html` identifies each by number.

## Printing

Validated offline using Bambu Studio {v['engine'].split()[-1]}, **0.16 mm High Quality**, 3 walls, 15% gyroid, Generic PLA. Select your actual filament and build plate; the validation assumed Textured PEI. Automatic rotation is off. Use build-plate tree supports on plates named `supports`, and inspect the resulting contacts. Plates named `flat` passed the geometric screen without generated supports. Flat does not mean every surface is horizontal.

Use a 3 mm brim where needed; the head platform and its peg sample benefit from 5 mm. Packed model bounds have 6 mm gaps, but brims/support trees can extend outside them. Inspect preview and separate objects if your settings produce conflicts. Remove supports and first-layer lips before fit testing. Do not globally scale parts to compensate for one tight joint.

| Batch | Plates | Estimated PLA | Estimated machine time |
|---|---:|---:|---:|
{chr(10).join(rows)}

Estimates include generated supports, brims and machine preparation; they are not measured results. No printer was contacted and no ready-to-run G-code is supplied.

| Family | Orientation / supports |
|---|---|
| Head, tail, pier cream halves | Broad central glue face down; whole foot keys share that face. No supports. |
| Hoops, flat colour inserts, threshold, handrails, loose keys and cradles | Keep supplied flat orientation; no supports. Handrail pins face up. |
| Tray | Flat underside down, open join pockets up; no bridge ceilings. |
| Sand | Visible ground face down; hidden glue recesses and registration sockets up. |
| Four beams and 14 long rail sections | Build-plate supports beneath curved surfaces; carefully clean the joint surfaces. |
| Two short upper rail end sections | Hidden flat faces down; no supports. |
| Slide shells and curved orange inserts | Supports on hidden underside/back; do not auto-rotate. |
| Head platform / peg sample | Rear edge down; supported locating pegs, 5 mm brim. |
| Ladder frame and tread comb / samples | Supports in supplied orientation. Remove completely before testing insertion. |

## What changed in the fits

| Interface | v03 seating and allowance |
|---|---|
| Hoop to beam | Two shoulders set height, 1.75 mm engagement, 0.15 mm per side/end, 0.20 mm bottom reserve; socket floors at least 1.20 mm. |
| Beam to pier | Flat underside blocks meet positive pier pads. Colour inlays clear the bearing. |
| Curved rails | Grooves follow actual curved rail and complete entry direction; checked minimum directional margin about 0.215 mm. End gaps 0.25 mm. |
| Feet through sand/tray | Whole pins/keys reach 4.2 mm below ground, with about 2.2 mm structural-tray engagement. Larger sand passages do not locate the feet. |
| Head platform | Complete vertical drop corridor, inward-open shelf slots; platform bears on shelves. |
| Tail / ladder | Rung18 has 0.20 mm side allowance at its positive landing. Handrails locate on cream pads through larger blue holes. Ladder comb has a direct insertion path with 0.30 mm nominal clearance. |
| Colour / sand inserts | Positive bearing lands/rims and 0.20 mm glue recesses establish face level. Sand uses a round locator plus a slotted locator. |
| Base halves | Close seam faces fully, then drop keys into open-top pockets. Sand covers the pockets. |

These are model allowances, not a claim about your printer's dimensional accuracy. The samples test surface finish, supports and filament behaviour that digital checks cannot.

## Assembly order

Dry-fit everything before glue. Use a small amount of PLA-compatible adhesive in recesses; keep bearing lands, shoulders, blind-hole bottoms and the assembly cradles clean.

1. **Base:** close the two tray seam faces fully on a flat surface. Drop in both join keys, then glue. Register each sand half on its round boss and slotted partner. The underside rim/pads establish height; glue the recesses without coating the datums.
2. **Cream laminations:** use the matching `test_jig_head_A/B`, `test_jig_pier_01..05` and `test_jig_tail_A/B` if helpful. Place the cosmetic outer/back half down with its central glue face up; place the keyed inner/front half on top. Push both feet gently toward the cradle's closed bottom stop, align the exposed outline and clamp. The open top allows vertical removal; these are alignment aids, not tight clamps. Remove the bare pair before adding colour inserts. Keep sides/numbers matched. Foot pins belong wholly to inner/front halves.
3. **Inlays:** seat each matching head, pier and tail insert on its small bearing lands. Put glue in the surrounding recess only. Cream handrail sockets must remain clear through the larger blue openings.
4. **Head:** lower the platform between the two panels. Its pegs enter the open shelf slots and the floor rests on both shelves. Dry-fit the whole head into the tray through the sand. Do not glue it down until the slides, body and ladder align.
5. **Body structure:** fit the four beam tongue joints and close their butt faces. Seat the beam on the five pier pads. Hoop01–17 keys enter their sockets until both shoulders sit on their ledges. Keep them dry while fitting rails. Beam01 takes hoops01–05, beam02 06–10, beam03 11–14, beam04 15–17. Piers01–05 are near hoops03,06,09,13,16.
6. **Rails:** lay each whole section into the outward-open grooves; do not thread it through the hoop. Tracks01/02 are upper left/right looking head-to-tail; 03/04 lower right/left. Sections01–04 follow that route. The upper tracks stop just after closed hoop15; lower tracks continue to rung18. Maintain the 0.25 mm end gaps and fully seated hoop shoulders. Glue only after all rails fit without bending them as levers.
7. **Tail:** drop the laminated walls onto the threshold tongues and their base keys. Rung18's flat sole rests on the low central landing at Z0.70. Check all three open U-rungs. Fit both handrail pins together; their collars rest on cream pads and establish stand-off through the oversized blue holes. The second socket allows slight pitch variation.
8. **Slides:** clean support marks on the curved inlays and pocket edges, then approach along each insert's midpoint outward normal in reverse until it touches its seating lands. Dry-fit the long toe keys: 2 mm into the slide and 4.2 mm below ground. Slide ground faces set height. Check slide tops, tail and ladder together before gluing.
9. **Ladder:** insert the cream comb straight into the blue frame at final height, seat it and glue. Dry-fit its lower feet on the sand and its upper end beside the platform; the upper interface has a small adhesive gap. Complete base glue joints only after the full structure sits correctly.

The 15 closed puffy hoops and three low open U-rungs remain deliberate. The visible style is retained; this revision changes manufacture and fit.
'''
(OUT/'README.md').write_text(text)
audit=json.loads((OUT/'validation/print-v03-audit.json').read_text())
assert not audit['unresolved_support_free_parts'],audit['unresolved_support_free_parts']
(OUT/'CANTILEVER-REVIEW.md').write_text(f'''# v03 support review

All {len(m['parts'])} actual individual STLs were screened in their supplied print orientations at 0.16 mm intervals, starting 0.10 mm above the bed. The screen checks new islands, growth beyond 45 degrees and downward-facing surface area. No piece labelled `supports: none` has an unresolved screen flag. This is geometric evidence, not a physical print guarantee.

{len(supported)} of the {len(prod)} production parts still deliberately require removable supports: four beams, fourteen long rails, two slide shells, four curved slide inserts, the head platform and the two ladder pieces. Actual support extrusion was verified on their packed plates by offline slicing. Representative supported joint samples retain these orientations and support requirements.

The revised base has open-top joining pockets, and the head shelf receivers open toward the printing top. Foot keys share their lamination's bed plane. Sand prints ground face down, so glue relief and blind registration cavities open upward. Alignment cradles have flat floors and vertical, open-top perimeter guides.

Inspect support contact in Bambu Studio and handle the narrow rails carefully. A successful slice does not establish that support cleanup leaves every joint accurate. Fit samples come first; read [FIT-TESTS.md](FIT-TESTS.md).

Detailed results and input hashes: [print-v03-audit.json](validation/print-v03-audit.json). Layer heuristic: 0.02 mm² reporting threshold, 45-degree growth limit; it does not simulate cooling, bridge sag, adhesion or support removal.
''')
print('Wrote v03 README and support review')
