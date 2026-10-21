# Entrance v03 fit corrections and validation

The v03 entrance fixes the tail and ladder defects identified in the v02 tolerance audit while preserving the approved tail silhouette and three open U-rungs. There are still 13 entrance/ladder production parts. This review covers this module; the complete kit's base integration, collisions and slicing are checked separately.

## Changed interfaces

| Interface | v03 correction |
|---|---|
| Rung 18 / threshold | At least 0.20 mm horizontal side allowance, with wider approximately 0.40 mm entry relief above Z2.05. The Z0.70 bearing is preserved. |
| Tail inlay depth | Three Ø2.4 mm seating lands per insert set the original visible relief. The rest of the pocket has 0.20 mm adhesive space. Edge clearance remains 0.15 mm per side. |
| Handrail / cream | Ø2.6 pins in Ø2.9 structural sockets; the second socket is elongated 0.6 mm along the pin pitch. Cream engagement is 1.5 mm with 0.20 mm blind-end reserve. |
| Handrail stand-off | Ø3.6 shoulders stop on raised cream pads, fixing the rail back 0.40 mm from the blue face. |
| Handrail / blue | Ø4.8 clearance openings, with the second also elongated. Nominal shoulder clearance is 0.60 mm per side, so the blue insert no longer determines the fit. |
| Tail / base | One whole 4 × 2 × 4.2 mm key per inner wall, with matching 4.3 × 2.3 mm sockets 4.4 mm deep in the cream base. Sand openings are 5 × 3 mm. Keys are coplanar with the print face and have 0.4 mm planar tip chamfers. |
| Ladder comb / frame | All seats open toward the headward side along a straight horizontal insertion path. Nominal clearance is 0.30 mm per side. Stringers are 3.0 mm diameter; treads are 5.8 mm wide. |
| Ladder / head | A true local clearance envelope removes the former edge contact and gives a minimum 0.20 mm gap. |

Tail base-key centres in the entrance coordinate frame are u=6 mm, n=+15.3 mm for side A and n=−15.3 mm for side B. Their top overlaps the cream wall by 0.8 mm and their tips end at Z−4.2. The exact base and sand cutters are returned by `entrance.build()` as `base_socket_cutters` and `sand_clearance_cutters`; use those solids, rather than recreating approximate placements.

The handrail's blue openings include enough margin for the nominal 0.15 mm inlay drift: approximately 0.60−0.15=0.45 mm per-side shoulder clearance remains. The structural sockets and stops belong entirely to the cream wall. The second slotted socket allows pitch mismatch without removing the first pin's locating function.

## Quantified verification

`python scripts/validate_entrance_v03.py` checks source solids and float32 STL round trips in memory. Passing `--assembly-dir` checks the final delivered STL triangles restored into assembly coordinates. It reads the matching manifest (or explicit `--manifest`) and screens the actual STL print meshes without exporting them again. Saved rotations and origins must recover those STL vertices and face indices. An optional `--json` writes its result; the command exits nonzero on a failed requirement.

The frozen v03 delivered-file run passed; its measurements and hashes are saved in `exports/dragon-pla-kit-v03/validation/entrance-v03-fit-audit.json`:

- All 13 delivered parts are connected, watertight, positive-volume solids.
- All 11 flat-printing tail parts passed horizontal-layer checks at 0.16 mm spacing for new islands and growth beyond the screened 45-degree limit. The two supported ladder parts are explicitly excluded from this no-support screen.
- Moving rung 18 by ±0.20 mm along either entrance axis, or along the tested diagonal, produces no side intersection above the landing. The current wider v03 sole retains approximately 37.05 mm² of bearing area at Z0.70.
- Handrail pin radial gap is approximately 0.14968 mm. Shoulder-to-blue clearance is approximately 0.59872 mm. A 0.01 mm press toward the wall encounters the cream shoulders, proving a positive stop; it does not depend on pin bottoming.
- Pressing either inlay 0.01 mm toward its floor encounters its three seating lands. The insert therefore cannot sink to the lower glue recess in the nominal geometry.
- The ladder comb's straight 12 mm approach was tested at 241 positions, 0.05 mm apart. Minimum sampled gap is 0.299997 mm, with zero intersections. Distance changes by no more than translation distance, so subtracting half the sample spacing and a 0.005 mm numerical allowance gives a conservative **0.269997 mm continuous-path clearance lower bound**, exceeding the 0.20 mm requirement.
- Frame/head minimum gap is 0.199998 mm against the final exported head geometry, matching the nominal 0.20 mm allowance within float32 accuracy.

The validator also exercises the second handrail pin at both ends of its ±0.30 mm pitch allowance: minimum remaining radial gap is approximately 0.14695 mm. Both blind-end reserves measure 0.200 mm. The delivered-file result applies to the audited hashes; changing an export requires repeating the audit.

## Assembly implications

Use the v03 external wall-half registration jig. Put inlay adhesive in the lower recess and leave the seating lands clean. Handrail shoulders seat on cream through the larger blue openings. The integral wall keys locate in the cream base; sand is a clearance layer. Keep the tail, threshold, last rung and slide loose during the first dry fit.

Assemble the ladder off the model: keep the comb at its final height and slide it horizontally from the headward side. A vertical drop or a push perpendicular to the ladder plane remains the wrong approach. Supports are still required on the ladder; this change resolves assembly access, not all support-removal concerns.

No physical PLA test has been performed. The relevant production coupons and mating pieces remain necessary to confirm actual material behaviour, support cleanup and glue handling. A successful slice is not physical fit validation.
