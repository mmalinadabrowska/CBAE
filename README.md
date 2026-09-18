# couldn't have been an email

A static landing page. Black on white, no framework, no build step.

```
index.html        the landing page
about.html        Who are we? — the studio and the four of us
manifesto.html    the manifesto, behind JOIN THE CONVERSATION
assets/css        layout, type and the photocopy ground
assets/svg        the hand-drawn marks and the texture
assets/fonts      Nudles and BBB Manifont Grotesk (licences alongside)
tools             the mark generator
```

Open `index.html` in a browser, or serve the folder (`python3 -m http.server`)
if you want the webfonts to load over http rather than `file://`.

## Type

- **Nudles Bold** sets the title and the page headings —
  <https://gitlab.com/bye-bye-binary/nudles>
- **BBB Manifont Grotesk** (Book and Book Italic) sets everything else,
  the manifesto included — <https://gitlab.com/bye-bye-binary/bbb-manifont-grotesk>

Both are self-hosted with their licences in `assets/fonts/`. Let Her Go, which
set the manifesto in an earlier version, is still in that folder but no longer
loaded.

## The hand-drawn marks

The red pencil ring around JOIN THE CONVERSATION, the ring around the date and
the close cross are vector strokes, not images. The ring is drawn the way a
pencil draws: a few light laps, each broken into segments, each sitting a
little off the last, over a shape that a slow wave pulls out of true.

They live in `assets/svg/` and are inlined into the pages between
`<!-- hw:name -->` markers, so they take `currentColor`. The pencil ring and the
date ring stretch to whatever the element measures and keep an even stroke
while they do.

```
python3 tools/handwriting.py
```

That rewrites `assets/svg/*.svg` and the inline copies in the HTML. The file
also holds a joined-up handwriting alphabet that can set any word as strokes —
that is how the title was drawn before it moved to Nudles.

## The photocopy ground

Two fixed layers on every page, both SVG, no bitmaps:

- `assets/svg/photocopy.svg` — the drag of the copier, long horizontal smears
  thresholded hard so most of the sheet stays white
- `assets/svg/toner.svg` — fine toner speckle, multiplied over the top

Both are kept light so the black text and the red pencil stay clean. They are
switched on by `<div class="paper"></div><div class="grain"></div>` at the top
of each page; remove the two divs for a plain white sheet, or tune the two
`opacity` values in `assets/css/style.css`.

## Placeholders

- `hello@couldnthavebeenanemail.com` — the address on the inner pages
- the manifesto text, and the studio line on Who are we?
- `28 OCTOBER` is set in `index.html`
