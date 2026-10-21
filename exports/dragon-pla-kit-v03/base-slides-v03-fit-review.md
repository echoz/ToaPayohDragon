# Base, piers and slides — v03 fit review

The final exported v03 package passes the independent checks after the pier and slide corrections. The final run restored the **actual delivered triangles of all 94 production STLs** using the print transforms in the frozen manifest, and recorded their SHA-256 hashes. These checks establish geometric fit and access; physical PLA fitting and support removal remain untested.

## Results

| Interface | Measured result |
|---|---|
| Five beam/pier bearings | Positive contact at the intended route Z−7.40 mm plane; sideways clearance approximately 0.216–0.301 mm per direction. Straight upward insertion/removal paths clear. |
| Five pier feet | Each engages the structural tray by **2.20 mm** through the sand layer. Tray clearance is **0.20 mm per side**; the separate sand passages provide **0.60 mm per side**. Ground faces establish height. |
| Ten pier inlays | Positive seating lands and clear outward installation paths. Top notches keep inserts clear of the beam landings and cream bearing pads. |
| Both sand halves | Rim/pads establish the intended Z=0 ground surface. Round-plus-slotted registration permits vertical placement without material obstruction. Peripheral movement is approximately 0.150 mm outward and along Y; movement toward the seam is limited at approximately 0.200 mm by the round locator. |
| Tray and sand seams | Closed in the intended assembly, with only float-rounding differences below 0.003 mm. This is a contacting seam, not a designed open gap. |
| Two tray joining keys | Approximately **0.20 mm per side** clearance, positive bottom seating and clear open-top installation. Install them before the sand. |
| Both slide toe keys | Each engages the tray by **2.20 mm**, with **0.20 mm per side** tray and slide-cavity clearance. Sand passage clearance is **0.60 mm per side**. Slide ground faces, rather than loose-key depth, establish height. |
| Four curved orange slide inserts | Positive lands establish the final visible face position; all four shared straight approach paths clear in the sampled check, including **slide2/left**. |

No integrated base/pier/slide overlap exceeded the report's **0.005 mm³ material-review threshold**. Residual numerical overlap at broad or curved contact surfaces is reported in the JSON rather than presented as exact zero. For example, the maximum slide2/left residual was 0.000673 mm³ and the largest slide-inlay residual was 0.001975 mm³ after float32 export. The source construction uses shared insert surfaces to avoid the earlier land penetration.

## Pier corrections made during this check

The whole foot key reaches the front lamination's t=0 printing face, removing the earlier above-bed cantilever. The key is unioned only after the front half is split: splitting a key lying on the central plane had left zero-volume remnants in the back half and failed the one-solid STL check. The resulting front key is 6.0 × 2.0 mm in plan and 4.2 mm deep below ground; matching tray and sand passages preserve the clearances above.

Beam clearances now project through the pier's full thickness, removing the roof that previously closed above the deep saddle near the outside face. Flat bearing pads are restored only at their intended height. Before projection, the beam envelope is clipped to the actual local pier thickness: the former world-axis bounding box included a lower neighbouring beam segment at the diagonal fifth pier, which had cut the bearing pad free. This local clipping resolved that disconnected pad.

All twenty pier pieces now remain single connected solids, survive float32 STL roundtrip and pass the flat-print overhang screen. The colour-inlay top notches keep the inserts clear of the new bearing arrangement.

## Slide wall and inlay checks

The slide pockets include the rigid insert's straight approach envelope, and seating lands establish the final position. The four inlays were translated outward along the same direction used to cut their pocket, in 0.10 mm increments through 3.2 mm. All passed the declared material-intersection threshold. Fit directions are recorded in the machine-readable results. Apply the inserts to each loose slide assembly before surrounding parts restrict hand access.

Normal-line sections sampled the remaining cream web at 18 route stations and three interior profile heights, on each side. There were **206 valid measurements** across both slides; ten positions outside intact inner-wall material or near trimmed edges were skipped. The lowest sampled widths from the nominal inner wall were:

- Slide1: **1.323 mm**, right side near 95% of the route.
- Slide2: **1.337 mm**, left side near 95% of the route.

These samples show that the pocket sweep has not broadly hollowed out the cheek walls. They are **not a proof of the minimum wall thickness everywhere**, particularly at profile edges, cutouts and head trims. The complete cream slides and curved orange inserts retain their support requirements.

## Print orientation and numerical limits

All **28 flat-designated pier, base and toe-key pieces** passed the successive-section screen: no new islands or excessive layer growth at the sampled 0.16 mm intervals. The two tray underside chamfers produced a few raw triangle-normal flags only about 0.001° beyond 45° after float32 rounding. Their layer-growth test was clean. The validator retains those raw metrics and uses an explicit **0.01° angular numerical allowance** when deciding whether the face flag is material.

First-contact probes use penetration above each pair's existing numerical contact baseline. This avoids mistaking a tiny rounded-coordinate overlap on a broad mating plane for zero horizontal clearance. Very small reported contact travel establishes an intended touching datum; it is not a printer-accuracy claim.

The source check builds the production geometry without creating sample pieces or changing output STLs. The script can repeat the checks against final restored meshes and actual print-oriented files:

```sh
.venv-print/bin/python scripts/validate_base_slides_v03.py \
  --assembly-dir exports/dragon-pla-kit-v03/work/assembly \
  --manifest exports/dragon-pla-kit-v03/manifest.json \
  --output exports/dragon-pla-kit-v03/validation/base-slides-v03-fit-audit.json
```

`test_*` copies are excluded from integrated collision checks. When manifest print transforms are available, the validator uses the actual STLs in preference to the assembly-preview meshes. Final passing results and file hashes are saved to `exports/dragon-pla-kit-v03/validation/base-slides-v03-fit-audit.json`. The earlier source/STL preflight remains in `work/base-slides-fit-validation.json`.

The checks do not simulate extrusion, glue-film thickness, thermal distortion, support-removal forces or every continuous assembly motion. A representative PLA fit print remains necessary before committing to the full set.
