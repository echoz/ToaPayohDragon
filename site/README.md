# Dragon project website

This directory is the standalone public website for Toa Payoh Dragon. It introduces
the v03 print candidate, shows actual CAD previews and links to its print kit and
guides. The intended published address is <https://echoz.github.io/ToaPayohDragon/>.

## Files and preview

- `index.html` owns the page content, navigation and kit links.
- `styles.css` owns the responsive layout, six-colour palette and decorative loops.
- `assets/` contains WebP encodings of the four original v03 preview PNGs.
- `.nojekyll` keeps this directory suitable for static GitHub Pages hosting.

No build step, JavaScript, external fonts, analytics or remote assets are required.
Serve this directory with any static HTTP server, for example
`python3 -m http.server 8000 --directory site` from the repository root. Open
`http://localhost:8000/`. Internal resources use relative paths for project hosting.

## Content and verification

The kit manifest and [print guide](../exports/dragon-pla-kit-v03/README.md) own
counts, colours and manufacturing details. The
[fit guide](../exports/dragon-pla-kit-v03/FIT-TESTS.md) owns the sample-first process.
Update the page when the candidate or its physical evidence changes. The website
must distinguish CAD renders, digital checks, offline slicing, physical printing,
physical fit and support removal. It does not grant a model or asset license.

Check local resource paths and fragment targets, keyboard navigation, visible
focus, reduced motion and mobile/desktop layout after changes. Confirm download
and guide links against the published repository when hosting is available.
Browser verification of this site does not validate the printable model.
