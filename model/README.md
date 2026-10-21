# Visual Blender authoring

This directory owns the editable visual model of the full Dragon Playground.
The approved visual revision is [v06](blender/dragon-puffy-hoops-v06.blend).
Its soft proportions and puffy hoops follow the approved concept; photographs
inform the layout. It is a visual prototype, not a set of printable solids.
The separately engineered [print geometry library](printkit/README.md) owns the
matching v03 printable parts and their interfaces.

## Entry point and composition

[blender_dragon_v06.py](blender_dragon_v06.py) owns `build()` and the main entry
point. It composes [head v04](blender_head_v04.py) and
[slide support v06](blender_slide_support_v06.py) with the body, supports, base,
materials, cameras and studio. The older head suffix is intentional: it remains
an active dependency of v06 and supplies profile data to the print library.

To regenerate, use `runpy.run_path('/absolute/path/to/checkout/model/blender_dragon_v06.py', run_name='__main__')` inside Blender through Blender MCP. Replace the example path with this checkout. `run_path` supplies `__file__`, which the script uses to locate the repository. Other Blender scripts use the same invocation with their own path.
It requires Blender's `bpy`, `bmesh` and `mathutils`; ordinary Python is insufficient. Confirm the MCP connection before a modeling or rendering operation.

Regeneration replaces the owned v06 scene and its objects, then overwrites
`blender/dragon-puffy-hoops-v06.blend` and `blender/build-v06.json`. Save manual
edits separately first. Other existing scenes are retained. Construction uses
estimated millimetre coordinates; the assembly parent converts to metres and
scales the playground length to 230 mm, excluding its base. Do not apply that
visual scale a second time to the final-millimetre print library.

## Review and limits

Use [validate_blender_review_v06.py](../scripts/validate_blender_review_v06.py)
inside Blender for targeted visual geometry checks. It writes
`blender/validation-v06.json`. The
[render script](../scripts/render_blender_review_v06.py) produces the review views;
the [design direction](../docs/design-direction.md) and
[nine-angle gallery](../renders/blender-v06/index.html) describe the existing
visual evidence. These checks do not prove assembly clearance or physical fit.

[extract_v06_print_source.py](../scripts/extract_v06_print_source.py) extracts
visual meshes for print engineering. It writes the retained
[source-v06 inputs](../exports/dragon-pla-kit/work/source-v06/); changing those
inputs requires a new print-geometry validation pass. For the existing printable
kit, use the [current fit instructions](../exports/dragon-pla-kit-v03/FIT-TESTS.md).
Physical PLA fit and support removal remain untested.

## Directory boundaries

`blender/` contains the two current saved scenes and generated visual reports.
The public checkout retains the active v06 model, v04 head and v06 slide support
sources. Earlier procedural versions, OpenSCAD scaffolding and output archives
remain in the original local authoring folder. Version suffixes here identify
active design dependencies, not interchangeable printable revisions.

The [project overview](../README.md) owns the release links and documentation gate.
The [toolchain guide](../scripts/README.md) owns export, validation and packaging
commands. Design history remains in [design-direction.md](../docs/design-direction.md);
its earlier status notes do not supersede the current kit manifest.
