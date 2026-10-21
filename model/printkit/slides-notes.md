# PLA slide module

`slides.py` preserves the v06 broad grounded support walls, stepped upper cutouts, raised/deeper toe and curved plan. Its eight printable parts are two cream structural slides, four orange inlays and two cream locating keys. No AMS is required.

The evaluated v06 channel and both cream walls are Boolean-unioned per slide. Orange skins are replaced by 1.20 mm solid curved inlays, with matching pockets and 0.15 mm clearance per edge. The nominal residual cream web is 1.41 mm. The cream margin and the orange face position follow v06.

A removable 4 × 6 × 4 mm rectangular key locates each thick toe in the base, nominally 2 mm into each side of the joint. Socket width/length are 0.30 mm larger than the key and depth has 0.20 mm allowance. Keys are separate so the slide's broad ground faces can sit directly on the print plate. The root build applies returned `base_socket_cutters` to the sand/base.

Call `build(head_obstacles)` with the union of completed head components. Slide tops and inlays are trimmed against that real geometry plus a 0.10 mm allowance toward the slide approach (negative X). Detached sub-1 mm³ Boolean offcuts are explicitly removed and reported. This replaces the visual prototype's overlapping assembly surfaces with a glue joint. The root build passes the actual head solids; a standalone call without them is only useful for source inspection.

The complete-kit build also passes `entrance_obstacles`, the union of finished tail and ladder pieces. Actual contacts receive localized relief cut with an exact 0.12 mm box offset, clearing the strengthened ladder rail and the tail wall beside slide 2. Relief volume is reported in the module metadata. The remaining approved slide profiles stay intact.

Print the cream slides upright, with their ground-bearing walls on the bed, using supports from the build plate under the raised head-end cutout/chute. A 3 mm brim is recommended. Orange inlays are oriented decorative face up and curved hidden back down; supports are required beneath portions of the curved back. Keep support scars on that hidden face, remove them completely, and dry-fit before gluing. Locating keys print flat without supports.

Verification: each finished part is a closed, consistently wound, single-component manifold. Mating head overlap and slide-part intersections are below 0.00001 mm³. The fit allowance and support removal still need a physical PLA test; slicer settings and final print validation belong to the complete kit package.
