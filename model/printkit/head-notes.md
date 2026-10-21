# Printable head — v03 fit revision

The head still has nine colour-separated parts: four cream laminations, two orange inserts, two blue inserts, and one cream platform/snout. Its visible v06 silhouette, paired splay, mouth, through-eye and raised cream eye surrounds are retained. Use only the matching v03 head and base interfaces.

## Flat head laminations and whole foot locators

Print all cream laminations on their broad central glue faces. Each inward cream half owns two **whole D-flat locating pins**; the outward cosmetic halves have no foot-pin material. The 3 mm pins have a 2.236 mm flat at the print/glue datum, remain connected directly to the inner foot, and end at assembly Z−4.2 mm. Their maximum initial outward profile slope is approximately 0.894, below the 45° screen. A flat pin nose avoids a narrow conical first-layer tip; entry guidance is provided by the tray socket mouth.

Use the separate head-outline lamination jig supplied by the parent kit to align the outward cosmetic half with its inner half. Use a thin glue film and keep the outline aligned while curing. Mechanical foot location and platform seating both belong to the inner halves, so a cosmetic glue seam no longer splits a locating pin.

Each foot uses one Ø3.4 mm round tray locator and one Ø3.4 mm capsule with 1.0 mm extra length along the pin-pair direction. This provides nominal 0.20 mm radial clearance and relieves the secondary pin's pitch constraint. Tray cutters extend to Z−4.5 mm, providing 0.30 mm tip allowance; the mouth has a lead-in near the Z−2 mm tray datum. With a 2 mm sand layer, the pin enters the tray by 2.2 mm, including the mouth lead-in. The sand layer uses separate Ø4.2 mm clearance holes/capsules, leaving nominal 0.60 mm per side around the 3 mm pin. The tray locates the head; the sand no longer acts as a second tight locator.

## Head colours and positive seating

The four coloured inserts remain 1.4 mm thick. Their perimeter, eye and shelf apertures use 0.20 mm side allowance. Each pocket contains three 2.2 mm seating lands at the intended back-face height, with 0.20 mm glue relief around them. Keep the lands clear of glue, place small adhesive amounts in the relief, and press the insert down to its lands. The visible face remains approximately 0.588 mm proud of the cream backing instead of sinking into an uncontrolled glue gap.

## Platform installation

The inward shelves now have **open U-slots**, not bridged horizontal blind bores. Each slot is 3.5 mm wide and 2.2 mm deep in assembly coordinates. It opens toward the centre of the head, which is upward in the flat panel's print orientation. Material below the slot is 1.2 mm thick. The platform's Ø3 mm pegs engage by 1.8 mm, leaving 0.25 mm lateral allowance and 0.40 mm bottom allowance. The broad shelf tops positively support the platform at Z40.0050634 mm.

The platform corridor is sized to the projecting inner cream eye rims with 0.30 mm normal clearance; its pegs are also moved inward. Drop the platform vertically between the head panels before fixing the head to the base. Its rear receiver is relieved by the continuous insertion sweep of hoop 01, plus 0.25 mm clearance. Install hoop 01 after the head platform.

Print the platform on its rear edge with a 5 mm brim and removable supports beneath its horizontal locating pegs. The new shelf slots remove the hole-crown bridge; they do not remove the platform's own support requirement.

## Verification and remaining physical checks

`scripts/validate_head_v03.py` checks source solids and binary STL roundtrips. It can also check the final exported parts with `--stl-root exports/dragon-pla-kit-v03`. It writes only audit JSON, not production STLs.

Current source, roundtrip and **actual exported STL** results: all nine head parts are watertight, positive-volume single solids; sampled platform insertion from +0.01 to +50 mm and hoop-01 insertion from +0.01 to +8 mm have zero overlap. All four coloured inserts have clear insertion paths and positive seating. Sand clearance slabs shifted ±0.30 mm in both X and Y remain clear of the whole foot pins within a 0.00001 mm³ numerical tolerance. Actual export hashes and measurements are recorded in `exports/dragon-pla-kit-v03/validation/head-v03-fit-audit.json`.

For the physical head check, print `test_head_A_shelf_slot` and `test_head_platform_peg_A` in their supplied orientations. Remove the peg's supports, then lower it into the slot: the plate underside should rest flat on the shelf without the peg bottoming out. Print `test_head_A_foot_inner` and `test_head_A_foot_outer`, align their flat backs and matching straight crop edges, and dry-clamp. Seat `test_head_A_sand` on `test_head_A_tray`, then lower the inner coupon's two whole pins through the sand into the tray; the foot shoulder should meet the sand without rocking. Try these fits before applying glue. These samples test the local joints; they do not replace the full-outline head jig or digital full-platform insertion check.

The parent kit must still verify the actual assembled v03 base and jig geometry and slice the final files. Physical PLA fit, supported-peg finish, glue thickness and support removal remain untested; use the representative v03 fit coupons before the full kit.
