# v03 assembly aids and base sample review

The frozen v03 delivered files passed this independent geometric review. Results are recorded in `exports/dragon-pla-kit-v03/validation/aids-v03-fit-audit.json`. The validator reads the exported STL triangles restored into assembly coordinates, takes jig placement transforms from the manifest, and verifies the NPZ vertices and face indices against the delivered STL. Its report records SHA-256 hashes for all 42 files involved.

## Lamination cradles

There are nine optional cream cradles: two heads, five piers and two tail walls. A narrow frame follows the complete outside silhouette, with 3 mm of material outside the outline and a 0.8 mm bearing rim inside it. The central area remains open beneath the head eye rims. A flat foot floor sets the thickness position, and the open-top cavity provides 0.15 mm side allowance. The floor is 1.2 mm thick.

The earlier foot-only cradle left the upper head free to turn far enough to move the horns about 1.3 mm. The complete perimeter now intercepts that rotation. Across the tested angular positions, the largest collision-free outline motion was 0.1673 mm for the heads, 0.1721 mm for the tail walls and 0.1426 mm for the piers. These are sampled geometric measurements, not a guarantee of clamp accuracy. Two loose halves can still occupy opposite sides of the 0.30 mm total lateral allowance.

All nine delivered jig STLs are watertight, connected solids. Whole production laminations fit at the manifest placement, and the sampled straight vertical placement/removal paths are clear. Nominal bearing produces only floating-point intersection residuals: the largest is 0.0000344 mm³ for a tail jig, below the audit's 0.001 mm³ numerical threshold. The lowest head relief remains 0.29079 mm above the bench; the other families remain approximately 1.20 mm above it. A downward floor probe confirms positive bearing of the lower half.

All nine cradles passed the 0.16 mm layer screen for new islands and growth beyond 45 degrees in the supplied print orientation. Head cradles use approximately 94 × 98 mm of the bed. The open centre avoids a floor collision under the raised eyes without requiring supports.

For assembly, place the bare outer/back half exterior down, add adhesive to its central flat mating face, and lay the inner/front half above it. Seat both outlines against the same side and foot datum; gently clamp the flat mating faces together. Keep glue out of the cradle. Lift the joined pair vertically and remove the cradle before installing colour inserts. The cradles are alignment aids, not tight clamps.

## Actual base and slide samples

The nine supplied samples include head-A tray/sand crops, the two base seam crops and their whole key, a round registration boss/socket pair, and the two full slide-2 parts. All nine delivered STLs are connected and watertight. The seven flat samples passed the no-support layer screen. The two slide parts retain their production orientations and support requirements; they are excluded from the no-support screen and can be reused in the completed model.

The two sand crops each add four 1.5 × 1.5 × 0.2 mm bearing pads to restore the production underside height. The measured addition is 1.8000004 mm³ per crop, spanning Z−2.00 to Z−1.80. Outside the prescribed pad windows, positive differences from the production sand are below 0.000035 mm³, attributable to float32 surface reconstruction. The pads do not change the tested holes, socket or mating profile.

| Delivered-file check | Result |
|---|---:|
| Head sample pads to actual head feet | 3.77332 mm minimum separation |
| Registration pads to raised socket boss | 5.62462 mm minimum separation |
| Sand pair downward 0.01 mm seating probe | 0.09000 mm³ bearing intersection |
| Sand pair sampled vertical placement | Clear, residual under 0.000002 mm³ |
| Closed seam separation | Below 0.000001 mm |
| Base key sampled vertical placement | Clear, residual under 0.000001 mm³ |

The crop pads therefore restore the intended datum without determining the head-pin or registration fit. The base seam faces set closure; the key locates and glues the closed seam. The complete slide samples use the actual production colour profiles, avoiding a shortened sample that could conceal a rigid insertion obstruction.

## Repeating the audit

```sh
.venv-print/bin/python scripts/validate_aids_v03.py \
  --assembly-dir exports/dragon-pla-kit-v03/work/assembly \
  --manifest exports/dragon-pla-kit-v03/manifest.json \
  --json exports/dragon-pla-kit-v03/validation/aids-v03-fit-audit.json
```

Omitting both input paths retains the source-build and float32 round-trip mode. `--jigs-only` limits either mode to the nine cradles. Missing delivered files, transform mismatches or failed geometric requirements stop the audit; delivered mode does not silently substitute source solids.

Physical PLA fit, support cleanup and glue/clamp handling remain untested. These aids and actual interface samples support the first dry fit; they do not replace it.
