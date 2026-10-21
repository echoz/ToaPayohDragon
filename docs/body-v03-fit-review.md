# Body v03 fit corrections and verification

The body changes correct the measured v02 tight spots and positioning gaps while retaining the approved route, colour sequence, 15 closed hoops and 3 open U-rungs. This report covers the body module. Whole-kit integration and offline slicing are recorded in the final kit; physical fitting remains untested.

| Interface | v02 finding | v03 change |
|---|---|---|
| Curved rail grooves | Four bend locations had only 0.072–0.115 mm side margin. | Actual curved rail envelope, with 0.20 mm target clearance, swept along a feasible insertion direction and projected through the flat printing thickness. |
| Rail butt ends | Twelve joins had 0.050 mm gaps. | All twelve use 0.250 mm gaps. |
| Hoop keys | Seventeen could drop 0.250 mm and tilt before rails/glue restrained them. | Wider 4.20 × 4.6311 mm keys retain 0.30 mm total insertion clearance; two shoulders establish height. |
| Key pocket floors | Flat pockets followed a sloping beam with limited floor allowance. | Local reinforcement provides a full 1.20 mm floor. |
| Beam-to-pier height | Clearanced curved saddles did not establish bearing height. | Five 5.2 × 3.0 mm underside landings have flat bottoms at route Z−7.40 mm; corresponding pier pads are implemented separately. |

The hoop bearing plane is route Z−3.00 mm. Keys end at Z−4.75 mm and sockets at Z−4.95 mm, leaving **0.20 mm bottom relief**. The shoulders, rather than key tips or a glue layer, establish height. The 1.75 mm key engagement remains a removable fit; stability comes from broad bearing surfaces, not an untested interference fit.

## Measured body-only checks

Current body solids were exported to float32 STL in their intended print orientations, then restored to assembly coordinates. All **38 pieces** remain single connected, positive-volume, watertight solids; no body/body overlap exceeded 0.001 mm³. Mesh topology retains the 15 closed loops and 3 open U-rungs.

- All seventeen shoulder seats establish height. Downward motion before contact was at most 0.000001 mm; this is a numerical contact result, not a printer-precision claim.
- Key width and axial clearances remain ±0.150 mm. All seventeen straight upward insertion/removal paths were clear in the sampled checks.
- Seated tilt probes on hoops02,11,16 contacted below 0.001°. Deliberately lifting them 0.10 mm away from the shoulders permits about 1.69° across the route and 2.48–2.51° along it. This demonstrates the seated datum while preserving removability.
- All key sockets retained their complete 1.20 mm floors in geometric volume checks.
- Minimum tested rail fitting margin across the 66 groove positions was **0.2149 mm**. Formerly tight side margins at track2/hoop11, track2/hoop12, track3/hoop11 and track3/hoop12 became approximately **0.270, 0.259, 0.226 and 0.232 mm**.
- All sixteen rail sections had clear sampled installation paths through 6 mm travel. All twelve end gaps measured 0.250 mm within STL rounding.
- All five underside landings retain their complete 5.2 × 3.0 mm bearing skins at route Z−7.40 mm.
- All eighteen hoops and two short upper rail stubs passed the 0.16 mm flat-print geometric screen: no flagged new islands, excessive section growth or downward faces over 45°.

The final delivered meshes passed at `exports/dragon-pla-kit-v03/validation/body-v03-fit-audit.json`. `work/assembly` now contains the actual exported STL triangles restored with their recorded print transforms; `validation/export-v03-audit.json` independently verifies those transforms and file hashes. Reproduce the check with:

```sh
.venv-print/bin/python scripts/validate_body_v03.py \
  --restored exports/dragon-pla-kit-v03/work/assembly \
  --manifest exports/dragon-pla-kit-v03/manifest.json
```

## Physical fit coverage and limits

`model/printkit/body_samples.py` returns six samples from production solids: hoop11, track02/section03, track03/section03, its cropped beam seat, and both cropped ends of the beam02/03 joint. Metadata states exactly where remote beam ends were clipped. Interfaces and print rotations remain unchanged, including their support requirements. The pier module can add a matching bearing pair.

Before full production, verify that real PLA samples seat without force, shoulders make stable contact, supported faces can be cleaned without changing the fit, curved rails enter along their intended path, and beam ends close against their butt faces. These behaviours have not yet been physically demonstrated.

The overhang screen and sampled insertion tests are geometric heuristics. They do not establish continuous motion in every direction, printer accuracy, glue-film behaviour, supported-surface finish or support-removal strength. Longer rails and beam modules still require supports.
