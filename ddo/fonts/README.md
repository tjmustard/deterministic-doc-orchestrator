# Bundled Fonts (hermeticity)

These fonts are bundled and pinned so Typst renders deterministically via
`--font-path ddo/fonts/` and never falls back to system fonts (SuperPRD §5,
Red Team #3).

## Contents

| Family | Files |
|---|---|
| DejaVu Sans | `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, `DejaVuSans-Oblique.ttf`, `DejaVuSans-BoldOblique.ttf` |
| DejaVu Serif | `DejaVuSerif.ttf`, `DejaVuSerif-Bold.ttf`, `DejaVuSerif-Italic.ttf`, `DejaVuSerif-BoldItalic.ttf` |
| DejaVu Sans Mono | `DejaVuSansMono.ttf`, `DejaVuSansMono-Bold.ttf` |

Template usage:
- `templates/typst/prd.typst` → `DejaVu Sans`
- `templates/typst/scientific_report.typst` → `DejaVu Serif`

## License

DejaVu Fonts. Free license derived from the Bitstream Vera Fonts Copyright and
the Arev Fonts Copyright. The fonts and derivatives may be used, studied,
modified, and redistributed freely, including bundling with software, provided
the fonts are not sold by themselves and the reserved font names are respected.

- Project: https://dejavu-fonts.github.io/
- License text: https://dejavu-fonts.github.io/License.html

Source on this build host: `/usr/share/fonts/truetype/dejavu/`.
