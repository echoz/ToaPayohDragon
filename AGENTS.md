# Toa Payoh Dragon

This repository is public. Keep the current source, matching v03 kit, its evidence
and approved visuals together. The original local authoring archive is separate.
Do not import old kits, research photographs, environment directories or backups.
The root README owns the source map; each declared deliverable has its own guide.

Use focused branches and pull requests. Credit Codex-assisted commits with
`Co-authored-by: Codex <codex@openai.com>`. Obtain separate engineering review
before readiness, and explicit user approval before merging.

Run `python3 scripts/check_documentation.py` and
`python3 scripts/check_publication.py`. The documentation checker needs the
separately installed, pinned private EngineeringRules bundle; public CI runs the
publication check. Follow `site/README.md` for visual and browser verification.
Python/HTML/CSS naming review is manual; this is not a Swift repository.

Geometry changes require the relevant delivered-STL and slicer audits described
in `scripts/README.md`. Never execute CAD scripts merely to discover their contents:
some write outputs on import. Preserve the accepted kit before regeneration.
Retain required source meshes and restored assembly meshes under `exports/`.

The website publishes only `site/`. Use actual CAD renders and label concepts
separately. Keep fit-test-candidate status and support requirements explicit.
Digital checks do not establish physical printing, fit or support removal.
