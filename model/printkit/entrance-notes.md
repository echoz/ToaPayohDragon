# Tail and ladder components — v03 fit revision

The photo-informed tail outline is preserved: two fuller peaked sidewalls, orange flame inlays outside, blue inside, two cream handrails and the three open U-rungs provided by the body module. The walls remain aligned with the last three stations' chord on the entrance route that eases inward by 6.6 mm. Main-body hoop placement is unchanged by this module.

## Walls, inlays and base registration

Each wall is two flat-backed 2.4 mm cream laminations. Use the matching v03 external registration jig when gluing their central faces. Each 1.2 mm colour insert retains 0.15 mm edge clearance per side. Three 2.4 mm diameter cream seating lands now stop it at its intended back plane, preserving 0.30 mm visible relief. Apply adhesive in the surrounding 0.20 mm recess, not on the lands. The blue insert has deliberately oversized handrail openings and does not locate the handrail.

Each inner cream wall half now carries one complete base key, 4 mm wide along the entrance and 2 mm thick, projecting 4.2 mm below the wall's ground face. It is centred at local entrance coordinate u=6 mm and lateral n=±15.3 mm. The key shares the half's print/glue plane and has a 0.4 mm planar chamfer at its tip; it creates no elevated first-layer island. Matching base sockets are 4.3 × 2.3 mm and 4.4 mm deep. The sand openings are 5 × 3 mm, with 0.50 mm per-side clearance, so the cream structure locates the wall. The ground faces of both wall halves seat on the sand. Use matching v03 base and sand parts.

## Handrails

Print each handrail's broad front face down with its posts upward. Two 3.6 mm shoulders pass through the blue clearance openings and bear directly on raised cream pads. These positive stops set the rail back 0.4 mm from the blue face. The blue openings are 4.8 mm across: nominally 0.60 mm radial clearance to a shoulder, retaining approximately 0.45 mm allowance after the insert's nominal 0.15 mm lateral drift.

The first structural cream socket is 2.9 mm diameter for a 2.6 mm pin. The second is a 2.9 mm wide capsule with an extra 0.6 mm length along the line between the pins, allowing ±0.30 mm pitch error. Both pins engage cream by 1.5 mm and retain 0.20 mm clearance to the blind floor after the shoulders seat. Dry-fit before applying glue. Press to the cream shoulders, not against the blue panel or blind-hole bottoms.

## Threshold and last rung

Print the threshold ground-face down. Its tongues enter the wall-bottom slots with 0.15/0.20 mm side clearances, 0.20 mm top room and 0.20 mm blind-end reserve. The centre retains the flat Z0.70 landing beneath rung 18's entire sole.

The raised sides now clear the rung by at least 0.20 mm horizontally. The upper 0.35 mm has a wider approximately 0.40 mm entry relief. This is an open stepped lead-in, not a friction-fit socket. Dry-fit the keyed walls, threshold, last rung and adjacent slide together before gluing.

## Ladder

The ladder remains two parts: a blue frame and a cream comb of nine 1.6 mm treads joined by a hidden 2 mm spine. Stringers are now 3.0 mm diameter and tread width is 5.8 mm. All nine seats are open horizontally from the headward side, with 0.30 mm nominal clearance per side along the demonstrated insertion path. Clean the supported faces, hold the treads at their final horizontal height, and slide the comb from the headward side into the frame. Assemble this subassembly before mounting it on the base; do not try to drop the comb vertically through the frame or push it perpendicular to the ladder plane.

Both ladder parts still require removable print supports and a brim. The frame's upper geometry clears the head by at least 0.20 mm; its feet provide the accessible base glue surfaces. Keep the ladder and head loose while setting the upper adhesive joint. The existing unsupported contact edge has been removed.

The module still has thirteen production parts. Source-solid fit checks, float32 STL round trips and the flat-tail print-layer screen pass. The ladder approach was checked across 12 mm at 0.05 mm increments, with a 0.300 mm minimum sampled gap and a conservative 0.270 mm lower bound between samples. Actual exported-STL checks are run again by `scripts/validate_entrance_v03.py --assembly-dir <restored-STL-NPZ-directory>`. These are digital checks; PLA fit and support cleanup require the production test pieces.
