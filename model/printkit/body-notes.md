# Body kit engineering notes — v03

`body.py` generates 38 separately printable solids: 15 closed hoops, 3 open U-rungs, 4 blue beam modules, and 16 blue rail sections. The first 15 approved v06 hoop positions and all colours remain. The last three stations follow a smooth 6.6 mm inward shift at the tail endpoint, giving the fuller entrance walls clearance beside the second slide.

Hoops 01–15 keep their closed oval outline. Stations 16–18 are low open U-rungs with rounded tips. A 0.45 mm rear-face slice provides the printing flat, shared by their keys and shoulders. Hidden 2.0 mm radius pads beneath the rounded tips extend to this plane. Rung18 retains its flat sole at assembly Z=0.70 mm for the tail landing. These are glue joints, not snap fits.

Hoops01–17 now have 4.20 mm wide keys, 4.6311 mm long along the route: `KEY_REAR=-2.3311`, `KEY_FRONT=2.30`. The key bottom is route Z−4.75 mm; the socket bottom is route Z−4.95 mm, preserving 0.20 mm bottom relief. Width and axial clearance remain 0.30 mm total, or 0.15 mm on each side/end. Two shoulder pads establish the height at route Z−3.00 mm, occupying lateral ranges −3.4 to −2.4 mm and +2.4 to +3.4 mm. The key does not bottom out. Seated engagement is 1.75 mm. Local beam reinforcement guarantees a full 1.20 mm socket floor even on the descending route.

The nominal 7.0 × 4.0 mm curved beam is split into four modules with 3.2 × 1.7 mm projecting tongues, matching 0.30 mm total-clearance sockets and 0.25 mm spare socket depth. Butt faces establish axial seating. Five underside landings at hoop stations3,6,9,13,16 are 5.2 mm across × 3.0 mm along the route, with flat bottoms at route Z−7.40 mm. This is exported as `PIER_BEARING_BOTTOM` and in `pier_seats`; the pier module supplies corresponding positive bearing pads. The beam stops before rung18, which instead rests on the tail landing.

Rails retain their 2.2 mm diameter. Grooves now follow an expanded copy of the actual sampled curved rail, with a target 0.20 mm per-side allowance and a small outward numerical guard. A continuous outward sweep defines a shared installation direction for each entire rail section. The cutter is projected through each hoop's print thickness, keeping the groove open with a constant printed section. The old straight 3.0 mm groove label no longer applies. Rail tags provide the installation vector; the bend's track03/section03 uses a slightly angled path. All twelve adjacent rail joins now have a 0.25 mm butt gap. Rails remain delicate until glued.

## Suggested print approach

- Hoops: provided flat orientation, rear face down. Their keys start on the same plane. A brim can help small keyed outlines. No generated supports are required by this orientation; verify the preview at the selected layer height.
- Beam modules: the provided orientation keeps top sockets visible. Removable supports are required beneath the curved underside. Keep the open key sockets free of support. Clean mating faces before dry fitting.
- Rail sections: the 14 long pieces retain removable supports and a brim. Upper tracks 01 and 02 stop just beyond closed hoop 15; their short section-04 pieces have 0.60 mm rear flats and print without supports. Lower tracks 03 and 04 continue through rung 18. Handle all rails gently and inspect toolpaths before printing.

## Assembly order

1. Print the fit sample and adjust clearances in CAD or by careful finishing if necessary. The numerical clearances are design assumptions, not physical calibration.
2. Dry-fit the four beam tongues and five positive pier bearings. Clean supported mating surfaces. Fit all members before gluing the beam into the structure.
3. Seat hoop01–17 shoulders fully on their beam ledges, keeping a thick glue layer out of the bottom relief. Leave them dry while checking rail fit; do not use a thin rail as an alignment lever.
4. Lay each complete rail section into its grooves along the recorded outward direction in reverse. Preserve the controlled end gaps. Glue only after verifying the seated hoop shoulders and all five pier bearings.
5. Glue the low last hoop onto its tail landing; no downward peg is present there.

## Digital checks

`scripts/validate_body_v03.py` checks actual float32 STL roundtrips, intersections, closed-loop topology, key clearances, shoulder-height stops, tilt, socket floors, rail margins/seams, whole-section insertion paths, pier landings and flat-print overhangs. It can run again on delivered restored STLs with `--restored` and `--manifest`. All 38 parts pass the current preflight. The 18 hoops and 2 short upper rail stubs pass the 0.16 mm flat-print geometric screen.

`body_samples.py` supplies six fit pieces directly from production solids: hoop11, the two formerly tight curved rail sections, its cropped beam seat and cropped beam02/03 joint ends. Crop metadata and production print orientations are preserved. These supplement the generic clearance coupon. Digital checks do not replace a physical PLA fit print or support-removal review.
