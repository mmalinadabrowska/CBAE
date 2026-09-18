# couldn't have been an email

A static landing page. Black on white, no framework, no build step.

```
index.html        the landing page
about.html        Who are we?
manifesto.html    the manifesto
assets/css        layout, type, and the photocopy texture from V1
assets/svg        the hand-drawn marks, generated
assets/fonts      Nudles, BBB Manifont Grotesk, Let Her Go (licences alongside)
tools             the mark generator
```

Open `index.html` in a browser, or serve the folder (`python3 -m http.server`)
if you want the webfonts to load over http rather than `file://`.

## Type

- **Nudles Bold** sets the title and the page headings —
  <https://gitlab.com/bye-bye-binary/nudles>
- **BBB Manifont Grotesk** (Book and Book Italic) sets everything else —
  <https://gitlab.com/bye-bye-binary/bbb-manifont-grotesk>
- **Let Her Go** sets the manifesto —
  <https://gitlab.com/bye-bye-binary/let-her-go>

All three are self-hosted with their licences in `assets/fonts/`.

## The hand-drawn marks

The red pill around JOIN THE CONVERSATION, the ring around the date and the
close cross are vector strokes, not images. They live in `assets/svg/` and are
inlined into the pages between `<!-- hw:name -->` markers, so they take
`currentColor`. The pill and the ring stretch to whatever the element measures
and keep an even stroke while they do.

```
python3 tools/handwriting.py
```

That rewrites `assets/svg/*.svg` and the inline copies in the HTML. The file
also holds a joined-up handwriting alphabet that can set any word as strokes —
that is how the title was drawn before it moved to Nudles.

## The photocopy texture

The first version sat on photocopied paper: toner mottle, grain and a riso
screen, all in CSS. It is still at the bottom of `assets/css/style.css`. Add
`<div class="paper"></div><div class="grain"></div>` back to a page to switch
it on.

## Placeholders

- `hello@couldnthavebeenanemail.com` — the address on the inner pages
- the about copy and the manifesto text
- `28 OCTOBER` is set in `index.html`
