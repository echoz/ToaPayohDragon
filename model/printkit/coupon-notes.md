# Three-piece PLA fit test

Print the cream `test_clearance_bar`, `test_hoop_02` and `test_head_pin_3mm` together at the kit's intended layer height (0.16 mm, with a 0.20 mm first layer in the validated profile), without supports. Their supplied orientation is ready for the plate. This coupon only screens nominal key/pin clearance; the v02 tolerance audit found additional assembly and seating defects it cannot validate.

The bar has four columns. One, two, three and four raised ticks identify total clearances of 0.20, 0.30, 0.40 and 0.50 mm respectively. Each column contains a rectangular pocket for the actual hoop key and a round pocket for a nominal 3 mm head pin. **Two ticks is the kit's current 0.30 mm clearance.**

The hoop is an exact copy of production hoop 02, including its key, rail grooves and flat rear printing face. Its rectangular key is 3.40 × (KEY_FRONT − KEY_REAR), approximately 3.98 mm, and the production beam engages about 1.65 mm of it. Coupon rectangle pockets are 1.90 mm deep. The handled 3 mm pin projects 2.40 mm; its coupon bores are 2.70 mm deep.

Remove any first-layer lip, strings and loose material without sanding the test dimensions away. Insert each probe with light finger pressure. Choose the smallest clearance that seats fully and can be removed. Do not force the hoop key into a tight pocket. A passing two-tick column does not release the full kit for printing: first resolve the v02 tolerance audit findings and test representative production joints in their actual print orientations. If another column is required, change mating dimensions or calibrated slicer compensation and rerun the coupon.

This checks nominal mating clearance, not the supported beam underside, the assembled seam of the split head pins, or glue strength. Actual head pins still need a dry fit after their cream halves are aligned and joined. Test pieces are separate from the finished model's part count; the hoop can be kept as a spare.
