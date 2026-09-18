# couldn't have been an email

A static landing page. Black ink on photocopied paper, no framework, no build step.

```
index.html        the landing page
about.html        who are we?
manifesto.html    the manifesto, set in Let Her Go
assets/css        paper, grain and layout
assets/svg        the handwritten marks, generated
assets/fonts      Let Her Go (see the licence in that folder)
tools             the handwriting generator
```

Open `index.html` in a browser, or serve the folder (`python3 -m http.server`)
if you want the webfont to load over http rather than `file://`.

## The handwriting

Every handwritten mark — the title, `JOIN THE CONVERSATION`, `get our mail`,
`who are we?`, the `x` and the `manifesto` heading — is vector strokes, not an
image and not a font. They live in `assets/svg/` and are inlined into the pages
between `<!-- hw:name -->` markers, so they inherit `currentColor`, scale to any
size and sit inside buttons.

They are drawn by `tools/handwriting.py`, which holds a monoline alphabet in
"pen units" (baseline at 0, x-height 10, ascender -21, cap height -15) and
shakes each letter by a fixed amount so the hand looks human but never re-rolls.

```
python3 tools/handwriting.py
```

That rewrites `assets/svg/*.svg` and the inline copies in the HTML. To change a
word, edit the `mark_*` functions at the bottom of the file; to change a letter,
edit `GLYPHS`.

## The texture

Three layers, all CSS, no bitmaps: a soft toner mottle and a copier streak on
`.paper`, fine grain and a riso screen set at 19° on `.grain`, and an SVG
`#toner` filter that roughens the edge of every ink stroke.

## Placeholders

- `hello@couldnthavebeenanemail.com` — the address behind `get our mail`
- the about copy and the manifesto text
