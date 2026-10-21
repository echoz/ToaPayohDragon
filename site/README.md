# Dragon project website

This directory is the standalone public website for Toa Payoh Dragon at
<https://echoz.github.io/ToaPayohDragon/>. It introduces the v03 print candidate,
shows actual CAD previews and links to its print kit, guides and license notices.

## Visual identity and files

The website has its own playground-inspired identity: cobalt blue, orange and white,
bold signage typography, rectangular display boards, mosaic grid accents and
geometric rib motifs. Its composition and styles are independent of Perch.

- `index.html` owns the content, navigation, image gallery and kit/license links.
- `styles.css` owns the responsive display boards, typography and decorative motifs.
- `assets/` contains unchanged WebP encodings of the four original v03 preview PNGs.
- `.nojekyll` keeps this directory suitable for static GitHub Pages hosting.

No build step, JavaScript, external fonts, analytics or remote assets are required.
Serve this directory with any static HTTP server, for example
`python3 -m http.server 8000 --directory site` from the repository root. Open
`http://localhost:8000/`. Internal resources use relative paths for project hosting.

## Content and licensing

The kit manifest and [print guide](../exports/dragon-pla-kit-v03/README.md) own
counts, colours and manufacturing details. The
[fit guide](../exports/dragon-pla-kit-v03/FIT-TESTS.md) owns the sample-first process.
Update the page when the candidate or its physical evidence changes. Keep CAD
renders, digital checks, offline slicing, physical printing, physical fit and
support removal distinct.

The root [license](../LICENSE.txt) and [scope notice](../LICENSE-SCOPE.md) are the
authority for licensing and attribution. CC BY-NC-SA 4.0 covers the original design
materials identified there. Scripts, build helpers and the HTML/CSS implementation
are excluded from that grant. The website links to both notices beside the kit
because the original v03 ZIP predates them. Keep that archive unchanged; recommend
saving both notices with the download. Future packages should include the notices.

## Verification

Run the repository's publication and documentation checks. Check resource paths,
fragment targets, keyboard navigation, visible focus and reduced-motion behaviour.
Review mobile, tablet and desktop layouts at 320, 390, 768 and 1280 pixels. Confirm
that the CAD images load and no page content causes horizontal scrolling. Verify
the download, guide, attribution and license links against the published repository.
Browser verification does not validate the printable model.
