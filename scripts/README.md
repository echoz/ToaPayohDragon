# CAD build, validation and packaging tools

These scripts turn the [print geometry library](../model/printkit/README.md) into
the v03 colour-separated STL kit and its evidence. They also support
[Blender visual authoring](../model/README.md) and public-delivery checks.
Individual pipeline stages are internal parts of this toolchain, not separately
versioned products.

## Environment and effects

Run shell examples from the workspace root. The geometry workflow uses the
`.venv-print/bin/python` environment with NumPy, trimesh, manifold3d
and Shapely. Environments are not included in Git. [requirements-print.txt](requirements-print.txt) records the authoring environment’s installed distributions; create a local Python virtual environment and install that snapshot before rebuilding. This is a dependency snapshot, not a tested cross-platform bootstrap.
Blender scripts require Blender and its MCP connection; slicing additionally
requires a local Bambu Studio app and its X1C profiles.

Most build and validation scripts write into `exports/dragon-pla-kit-v03/`.
Some run at import time. Do not import stages as a discovery mechanism or run
them merely to check documentation. Preserve a completed kit before regeneration:
the current output directory and ZIP names are fixed, and existing results can
be overwritten. Source-only checks are not equivalent to auditing delivered STLs.

## Regeneration workflow

1. Inspect the source changes and retained
   [visual mesh inputs](../exports/dragon-pla-kit/work/source-v06/). Blender source
   extraction is a separate, mutating operation; it is not needed for every print
   revision.
2. Run `.venv-print/bin/python scripts/build_print_kit.py` to export parts, fit
   samples, cradles, layouts, the manifest and actual-STL assembly meshes.
   `--audit-only` still builds geometry and writes an interference report; it is
   not a read-only documentation check.
3. Validate the delivered geometry using the entry points below. Keep the
   manifest, STLs and restored meshes from the same build. These commands write
   reports and can be expensive.
4. Run `.venv-print/bin/python scripts/audit_print_v03.py` for the all-part layer
   and overhang screen. It still uses the helper in `audit_tail_v02.py`; that file
   is an active dependency despite its suffix.
5. Run `.venv-print/bin/python scripts/slice_print_kit.py` for offline slicing,
   followed by `scripts/summarize_print_slicing.py` with the same Python. The
   slicer accepts `--app /path/to/BambuStudio.app`, `--prepare-only` and optional
   STL paths. A complete release needs every manifest layout. It does not send
   jobs to a printer and normally removes temporary G-code.
6. Run `scripts/finalize_v03_validation.py` only after all required reports and
   slicing pass. Then run `scripts/write_v03_guide.py` and
   `scripts/print_kit_maps.py` with the same Python to update the guides and maps.
   Finalization records digital status; it does not certify a physical print.
7. Run [preview_print_kit.py](preview_print_kit.py) inside Blender via MCP to
   produce a separate printable-assembly scene and previews from actual exported
   meshes. It requires the v06 visual scene and refuses to replace an existing
   `Dragon • Fit Revision 03` scene; inspect that scene before deciding how to
   regenerate it. Let rendering finish before packaging.
8. Run `.venv-print/bin/python scripts/package_print_kit.py` after checking the
   guide, previews and evidence. It verifies recorded STL hashes, copies slicer
   evidence, writes final checksums and replaces `exports/dragon-pla-kit-v03.zip`.
   Reference photographs and build scratch are excluded.

The packager requires the root `LICENSE.txt` and `LICENSE-SCOPE.md`, copies both
into the package and covers them in its checksums. The currently published v03
archive predates those notices and remains unchanged; its root-level notices
apply to the covered materials inside it. Do not run the packager over that
published artifact merely to add notices. Prepare a separately identified future
candidate and update the fixed output paths before publishing a rebuilt package.

Delivered-geometry audit commands:

```sh
.venv-print/bin/python scripts/validate_export_v03.py
.venv-print/bin/python scripts/validate_body_v03.py --restored exports/dragon-pla-kit-v03/work/assembly --manifest exports/dragon-pla-kit-v03/manifest.json --output exports/dragon-pla-kit-v03/validation/body-v03-fit-audit.json
.venv-print/bin/python scripts/validate_head_v03.py --stl-root exports/dragon-pla-kit-v03 --out exports/dragon-pla-kit-v03/validation/head-v03-fit-audit.json
.venv-print/bin/python scripts/validate_entrance_v03.py --assembly-dir exports/dragon-pla-kit-v03/work/assembly --manifest exports/dragon-pla-kit-v03/manifest.json --json exports/dragon-pla-kit-v03/validation/entrance-v03-fit-audit.json
.venv-print/bin/python scripts/validate_base_slides_v03.py --assembly-dir exports/dragon-pla-kit-v03/work/assembly --manifest exports/dragon-pla-kit-v03/manifest.json --output exports/dragon-pla-kit-v03/validation/base-slides-v03-fit-audit.json
.venv-print/bin/python scripts/validate_aids_v03.py --assembly-dir exports/dragon-pla-kit-v03/work/assembly --manifest exports/dragon-pla-kit-v03/manifest.json --json exports/dragon-pla-kit-v03/validation/aids-v03-fit-audit.json
```

The [v03 tolerance review](../docs/tolerance-corrections-v03.md) states the
geometric checks and their limits. Offline slicing does not prove cooling,
adhesion, support removal or physical fit. Use the
[fit-test guide](../exports/dragon-pla-kit-v03/FIT-TESTS.md) before a full print.
For changes limited to these authoring guides, run the documentation gate below;
the completed kit's geometry and slicer evidence does not need regeneration.

## Documentation gate and review

Run `python3 scripts/check_documentation.py` before completing changes to the
configured authoring guides or deliverable inventory. `--format json` returns
machine-readable findings. The wrapper resolves this workspace from its own path,
so it also works when invoked by absolute path from another directory.

[check_documentation.py](check_documentation.py) pins EngineeringRules 0.1.11 at
`3e42da0e724fe54585cc3cdd9009c749f7ba24d9`. It uses the existing checkout at
`~/.local/share/engineering-rules/0.1.11` and its `.build/docs-venv/bin/python`,
verifies HEAD and the checker file against that revision, and runs the checker
without installing or updating anything. Python 3.9+ and Git are needed for the
wrapper; the checker requires its release-pinned Markdown parser dependencies.
A missing environment or changed pin is an error, not a skipped pass. Follow the
[release installation contract](https://github.com/echoz/EngineeringRules/blob/3e42da0e724fe54585cc3cdd9009c749f7ba24d9/README.md)
when provisioning another machine; do not copy an unpinned checker into Dragon.

Exit 0 means the configured documentation scope passed, 1 means findings, and 2
means configuration, dependency or wrapper failure. The
[schema 2 inventory](../.documentation-rules.json) checks four distinct
source-root READMEs plus the project overview and license scope notice. It has no directory-module
inventory or exclusions: the current Python stages and geometry helpers share
their owners' guides. This is not an automatic inventory of every file.

Use the installed `engineering-review` skill for separate review. It checks actual
deliverable ownership, useful guide content and the applicable organization,
behavior/compatibility, data/effects, tests/evidence and documentation contracts.
Dragon is tracked in the public `echoz/ToaPayohDragon` repository. Use a focused
branch and pull request for new changes, and the skill's Git evidence helper with
the actual PR base, planned checks and independent review. The earlier manual
reports describe the pre-Git workspace; retain them as historical evidence rather
than treating them as fresh review of later changes. A link check does not prove
CAD correctness. No SwiftRules configuration is applicable to this toolchain.

The public repository is the active source for published changes. The separate
local authoring archive retains its own documentation wrapper and three-deliverable
inventory for historical work. Both wrappers target the same 0.1.11 source release;
the archive is checked separately and is not part of this repository's Git review.
Version 0.1.11 leaves the documentation checker, schema 2 and review skill unchanged.
The separately installed 0.1.9 review skill matches the 0.1.11 payload; keep its
verified installation hashes with private review evidence and reload the owning
engineering and organization guidance.

The release's optional `compilerProfiles` workflow is for native Swift witness
analysis and does not apply to this Python/CAD toolchain. No Swift tool version,
compiler exporter or witness context is enrolled.
Run the existing documentation and publication gates for this adoption.

### Manual naming review

EngineeringRules 0.1.8 adds a Swift declaration inventory named
`review-candidates`; it does not collect Dragon's Python or OpenSCAD names.
Review owned names manually under the global organization guidance. Collect
source locations and relevant callers before judging a name. Inspect the meaning
of declarations, framework references and persisted keys, including lowercase
`context` spellings. Text search supplies leads, not a semantic verdict.

Review all introduced or changed declarations and bindings, including unchanged
names whose meaning changes; a `Context` search alone is insufficient. Keep the
scoped inventory and source hashes with the exact candidate's review evidence.
The independent reviewer records a concrete rename within scope,
a legitimate retain reason, or an explicit deferral and its boundary for each
candidate. A successful search does not complete that review, and a deferral does
not create a permanent waiver or naming baseline.

For identity and revision names, inspect their creation and comparison sites and
any advancement or invalidation. Apply the owning organization guidance to their
subject and lifetime. This adoption retains the wrapper's tool version, exact
source revision and observed checkout revision as distinct facts; it does not
change application identities or constitute a new naming audit of the CAD source.

Current CAD naming judgments:

| Name or usage | Judgment and evidence |
| --- | --- |
| `bpy.context` | Retain Blender's framework API for the active window, scene, view layer and evaluated dependency graph. See [visual authoring](../model/blender_dragon_v06.py), [visual validation](validate_blender_review_v06.py) and [preview import](preview_print_kit.py). Earlier revision scripts use the same API. These are references, not owned context types. |
| `fixture_context` | Defer renaming or replacing this persisted tag outside the documentation/pin update. [base_samples.py](../model/printkit/base_samples.py) describes added bearing pads or an unmodified crop; [build_print_kit.py](build_print_kit.py) exports the tag, and [validate_aids_v03.py](validate_aids_v03.py) uses it to select pad checks. A redesign needs coordinated producer, consumer, manifest and validation changes; preserve the current v03 identity. |
| `context` in fixture, map and reference prose | Retain ordinary descriptions of fixture modifications, positional surroundings and historical/reference background. These do not name bundled state or dependencies. |

The adoption inventory found no owned declaration matching capitalized `Context`.
That finding is bounded to the reviewed source snapshot. Historical archives,
generated files, saved Blender scenes, downloaded references and dependencies are
outside naming-refactor scope; inspect them only as needed to establish a contract.
Text/AST inspection does not cover dynamic declarations or establish complete
semantic name discovery. Swift's collector also omits references, value/function
names, comments, strings and expanded declarations. Record these coverage limits
in each review and preserve the source-root documentation gate above.

## Public delivery and history

[check_publication.py](check_publication.py) checks public-file boundaries, local
Markdown and HTML links, Python syntax, and the retained v03 checksums without
executing CAD. Run it with `python3 scripts/check_publication.py`. The Pages
workflow runs it before uploading only `site/`; `site/README.md` owns the browser
checks and visual composition. Review binaries and prose before publication;
a pattern scan cannot prove that all sensitive material is absent.

Reference collection tools, earlier Blender versions and old print-kit snapshots
remain in the original local authoring archive. `audit_tail_v02.py` remains an
active dependency of the current v03 audit despite its name. The public checkout
includes the current matching kit and required build inputs, not the full archive.

The public import changes authoring-root lookup to use each script’s `__file__`
and restores assembly preview paths relative to the current kit. Geometry
expressions and delivered artifacts are unchanged. Run Blender entry points
through `runpy.run_path` as shown in the visual authoring guide; bare `exec` needs
an explicit `__file__` in its namespace. Rebuilding and live Blender execution
have not been repeated for the publication-only changes.
