# Head v03 fit revision — source and STL validation

The documented head-platform insertion collision and the split-foot-pin design have been corrected in `model/printkit/head.py`. The approved visible head silhouette remains. There are still nine head parts; no extra loose head pins or trim pieces were introduced. The archived v02 kit is unchanged; final v03 production STLs have been exported and checked as described below.

## Changes

| Interface | v03 design |
|---|---|
| Platform corridor | Sized to the inner cream eye surround, with 0.30 mm normal allowance, instead of to the thinner blue face. Peg centres also move inward. |
| Shelf location | Inward-open U-slots, 3.5 mm wide × 2.2 mm deep; no horizontal bore crown. 1.2 mm material remains below the slot. |
| Platform seating | Original Z40.0050634 mm shelf datum retained. Ø3 mm pegs engage 1.8 mm, giving 0.25 mm per side and 0.40 mm bottom allowance. |
| First-hoop receiver | Continuous vertical sweep plus 0.25 mm XYZ clearance, rather than a cut based only on the final pose. |
| Foot pins | Whole Ø3 mm D-flat pins on each **inner** cream half only. Pin centre offset is 1.0 mm into that half; flat chord is 2.236 mm. Tips end at Z−4.2 mm. |
| Tray location | One Ø3.4 mm round socket and one 3.4 mm-wide capsule with 1.0 mm extra length per foot. Socket depth 4.5 mm, mouth lead-in, 0.30 mm bottom allowance. |
| Sand clearance | Separate Ø4.2 mm openings, with the secondary openings elongated to match the tray slots. Nominal radial allowance is 0.60 mm, so the sand does not tightly locate the pins. |
| Coloured inserts | 1.4 mm thickness retained; 0.20 mm lateral allowance. Three 2.2 mm lands establish each back-face datum, with 0.20 mm glue relief around them. Intended visible face level is retained. |
| Lamination alignment | Mechanical pins no longer depend on the cosmetic glue seam. The parent kit supplies external head-outline jigs for the remaining cosmetic-half alignment. No bed-side pegs are added. |

The whole D-flat pin is clipped at the glue/build plane and joins the inner foot at the ground shoulder. Its lower cylinder's maximum outward growth slope is `1 / sqrt(1.5² − 1²) = 0.894`, below the 45° screening limit. Keeping the pin nose flat avoids a thinner conical end with steeper initial growth. The female socket supplies the entry lead-in. The source and roundtrip solids both have one connected component after this change.

The head-base cutter API is now:

- `base_socket_cutters`: precise tray locators, with lead-ins and round/slot pairing.
- `sand_clearance_cutters`: larger non-locating openings for the sand layer.
- `foot_pin_shapes`: exact whole D-pin shapes for representative fixture tests.
- `metadata.foot_pins`: final centres, pin dimensions, slot direction, depths and lead-in dimensions.
- `metadata.platform_shelves`: final peg centres, slot direction, width, depth and floor thickness.

Do not reuse v02 foot-hole centres. The new A-side centres are approximately **(84.020755, 18.751937)** and **(91.508334, 14.633769)** mm; B mirrors Y. The 2.2 mm engagement beyond a nominal 2 mm sand sheet includes the tray-mouth lead-in, leaving approximately 1.75 mm in the straight locator region.

## Validation performed

The reproducible check is `scripts/validate_head_v03.py`. It builds only the head and the first body hoop needed for its receiver test. Its default mode serializes binary STL in memory, reads those exact triangles back and restores assembly coordinates. It also supports `--stl-root` to read actual exported files.

The **actual exported v03 STLs** have now passed this check using `--stl-root exports/dragon-pla-kit-v03`. Their file hashes and measurements are saved in [head-v03-fit-audit.json](validation/head-v03-fit-audit.json). The earlier in-memory report remains in `head-fit-validation.json` (workspace-only evidence). The validator writes audit JSON only.

| Check | Source geometry | Actual exported STL |
|---|---:|---:|
| Platform top-drop, +0.01–50 mm, 0.125 mm samples | 0.0 mm³ maximum overlap | 0.0 mm³ maximum overlap |
| First-hoop downward installation, +0.01–8 mm, 0.05 mm samples | 0.0 mm³ maximum overlap | 0.0 mm³ maximum overlap |
| Four coloured-insert normal insertion paths | 0.0 mm³ maximum overlap | 0.0 mm³ maximum overlap |
| Platform seated against shelves | 0.0 mm³ overlap | 0.0 mm³ overlap |
| Outer-half material below Z−0.01 mm | None | None |
| Inner-half pin tip height | −4.2 mm | −4.2 mm |

All nine head components and the tested first hoop are watertight single solids. The maximum source-to-STL dimensional difference was approximately **0.00000312 mm**. Raw contact artifacts in the independent sand fixture were at most **0.00000431 mm³**, below the **0.00001 mm³** test threshold.

The ground-interface check uses an independent fixed tray slab cut with the returned production tray cutters, plus a separate sand slab cut with the returned sand cutters. There is no tray/pin overlap. Moving that sand slab by each combination of X/Y = −0.30, 0 and +0.30 mm causes no meaningful pin interference. This directly exercises the independent-layer clearance that was missing in v02, but it is not a substitute for checking the parent kit's actual base solids.

The receiver is constructed from a continuous vertical sweep, and the platform corridor is limited by the most protruding inner eye surface. The sampled source/STL checks confirm the exported representation; they do not claim to exhaust every tilted or sideways hand motion.

## Remaining integration and physical work

`model/printkit/head_samples.py` supplies four small fit samples cropped from the production solids, preserving each production print orientation:

- `test_head_A_shelf_slot` and `test_head_platform_peg_A` test the open shelf, supported peg finish, lateral clearance and positive seating. The peg crop retains the platform's support requirement. The pair has zero overlap throughout a 0–10 mm vertical insertion check at 0.125 mm increments.
- `test_head_A_foot_inner` and `test_head_A_foot_outer` preserve both complete A-side pins, the original glue faces and matching straight crop edges. They test the whole-pin print geometry, pin pitch and cosmetic-half assembly when combined with the parent kit's actual tray/sand fixture. Their seated overlap is below 0.000000000001 mm³.

All four samples passed watertight, positive-volume, single-component checks after binary STL roundtrip. Their combined CAD volume is approximately 1.53 cm³. They do not replace the full-platform eye-clearance test, four-pin global span check or full-outline lamination jig.

The parent kit records passed integrated tray/sand and jig audits, global assembly checks and offline slicing in its final validation reports. The head STL audit is complete for the hashes recorded in its report; changes to those files require rerunning it. The platform retains removable supports under its pegs. Physical PLA clearances, supported surface finish, adhesive handling and support removal are still untested.
