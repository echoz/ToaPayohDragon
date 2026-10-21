# v03 support review

All 132 actual individual STLs were screened in their supplied print orientations at 0.16 mm intervals, starting 0.10 mm above the bed. The screen checks new islands, growth beyond 45 degrees and downward-facing surface area. No piece labelled `supports: none` has an unresolved screen flag. This is geometric evidence, not a physical print guarantee.

27 of the 94 production parts still deliberately require removable supports: four beams, fourteen long rails, two slide shells, four curved slide inserts, the head platform and the two ladder pieces. Actual support extrusion was verified on their packed plates by offline slicing. Representative supported joint samples retain these orientations and support requirements.

The revised base has open-top joining pockets, and the head shelf receivers open toward the printing top. Foot keys share their lamination's bed plane. Sand prints ground face down, so glue relief and blind registration cavities open upward. Alignment cradles have flat floors and vertical, open-top perimeter guides.

Inspect support contact in Bambu Studio and handle the narrow rails carefully. A successful slice does not establish that support cleanup leaves every joint accurate. Fit samples come first; read [FIT-TESTS.md](FIT-TESTS.md).

Detailed results and input hashes: [print-v03-audit.json](validation/print-v03-audit.json). Layer heuristic: 0.02 mm² reporting threshold, 45-degree growth limit; it does not simulate cooling, bridge sag, adhesion or support removal.
