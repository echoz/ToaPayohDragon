# Printable geometry library

This directory owns the final-millimetre solids for the colour-separated v03 PLA
kit. It translates the approved visual design into separate parts, mating
interfaces, representative fit samples and optional assembly cradles. Its direct
consumer is [build_print_kit.py](../../scripts/build_print_kit.py).
The [visual authoring guide](../README.md) describes the upstream Blender model.

## Use and composition

Use the [toolchain workflow](../../scripts/README.md) to build a complete matching
set. For inspection from the workspace root, the library can also be imported in
Python, for example `from model.printkit import body`. Calling `body.build()`
constructs its parts and metadata in memory; exporting belongs to the toolchain.
The geometry environment needs NumPy, trimesh, manifold3d and Shapely; see the toolchain guide for the authoring-machine dependency snapshot. Blender is not needed for these solid builders.

[common.py](common.py) owns the `Part` record, colours, geometry helpers, route
and retained [source mesh inputs](../../exports/dragon-pla-kit/work/source-v06/).
`Part` carries a name, colour, solid, optional print orientation, support guidance,
notes and tags. Orientation maps assembly coordinates to the print bed; exported
parts must retain their recorded transforms and 100% scale.

| Owner | Responsibility |
| --- | --- |
| [body.py](body.py) | Puffy hoops, rails and body connections. |
| [head.py](head.py) | Head laminations, colour inserts, platform and locating feet. |
| [entrance.py](entrance.py) | Tail walls, entrance and ladder. |
| [slides.py](slides.py) | Slide channels and side walls, composed against head and entrance solids. |
| [supports_base.py](supports_base.py) | Piers, structural tray, sand layers and base join. |
| [coupon.py](coupon.py), [body_samples.py](body_samples.py), [head_samples.py](head_samples.py), [entrance_samples.py](entrance_samples.py), [base_samples.py](base_samples.py) | Clearance coupons and representative joints derived from the assembled parts. |
| [assembly_aids.py](assembly_aids.py) | Optional cradles for aligning glued laminations. |

The build coordinator assembles the families in dependency order. Returned
socket cutters describe tight structural-tray locations; separate sand cutters
give the decorative layer clearance. Slides consume head/entrance geometry and
piers consume body beams. Building one family alone does not check those joins.
The shared nominal clearance is not a universal tolerance: each interface has
its own geometry and fit evidence.

## Verification and limits

The [v03 tolerance review](../../docs/tolerance-corrections-v03.md) owns the
corrected interface rationale and links the delivered-mesh audits. Family reviews
cover [body](../../docs/body-v03-fit-review.md),
[head](../../docs/head-v03-fit-review.md),
[entrance](../../docs/entrance-v03-fit-review.md),
[base/slides](../../docs/base-slides-v03-fit-review.md) and
[assembly aids](../../docs/aids-v03-review.md). The toolchain validates actual
exported STL triangles restored to assembly coordinates, in addition to source
solids. Recheck affected interfaces, insertion paths, seating, print orientation
and slicer results after changing geometry or source meshes.

Current evidence is digital. Print the [matching fit samples](../../exports/dragon-pla-kit-v03/FIT-TESTS.md)
on the X1 Carbon with its 0.4 mm nozzle and PLA before the whole kit. Physical
printing, fit and support removal remain unverified. The
[kit guide](../../exports/dragon-pla-kit-v03/README.md) owns settings and assembly.

Earlier print-library snapshots remain in the original local authoring archive.
Do not mix their mating parts with v03. Local family notes preserve design
development; the current manifest and v03 reviews establish the matching set.
