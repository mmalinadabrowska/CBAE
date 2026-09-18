#!/usr/bin/env python3
"""Draws the site's hand-drawn marks as vector strokes.

The marks the site uses today are shapes: the red pill around JOIN THE
CONVERSATION, the ring around the date and the close cross. The joined-up
alphabet below is kept because it can set any word as strokes, the way the
first version of the title did.

Coordinates are in "pen units": the baseline is y = 0, y grows downwards,
x-height is 10, the ascender reaches -21, the cap height is -15.

Run `python3 tools/handwriting.py` after changing a glyph. It rewrites the
SVG files in assets/svg/ and the inline copies between the
`<!-- hw:name -->` / `<!-- /hw:name -->` markers in the HTML pages.
"""

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "assets" / "svg"

X_HEIGHT = 10.0
SLANT_DEG = 9.0          # forward slope of the hand
LETTER_SPACING = 1.6
JOIN_SPACING = 1.5     # the ligature between joined-up letters
WORD_SPACING = 9.0

# --- the alphabet -----------------------------------------------------------
# name: (advance width, [subpath, ...]). Absolute M/L/C/Z commands only.

# Lowercase is joined-up: every letter is one stroke that starts on the
# baseline at (0, 0) and leaves it again at (width, 0), so letters in a word
# run into each other the way a fast hand writes them. A few marks — the
# apostrophe, the question mark, the dot on the i, the cross on the t — are
# drawn with the pen lifted and listed after the joining stroke.

DETACHED = set("'?.,")

# letters whose stroke ends up at x-height; the join then swings back down
EXIT_Y = {"o": -6.2, "v": -7.6, "w": -7.6, "b": -5.2}

GLYPHS = {
    "a": (9.2, [
        "M 0,0 C 1.2,-2.4 2.8,-6.2 4.4,-8.0 C 5.4,-9.0 6.6,-8.6 6.9,-7.0 C 7.2,-5.4 6.6,-2.8 5.4,-1.4 C 4.2,-0.1 2.6,-0.5 2.1,-2.0 C 1.7,-3.4 2.4,-5.2 3.6,-6.2 C 4.6,-7.0 5.8,-7.2 6.6,-6.6 C 6.6,-4.6 6.4,-2.4 6.5,-1.2 C 6.6,-0.4 7.0,-0.1 7.7,-0.3 C 8.4,-0.5 8.9,-0.9 9.2,-1.3"
    ]),
    "b": (9.0, [
        "M 0,0 C 1.2,-5 2.6,-12 3.6,-17 C 4.1,-19.4 4.5,-20.8 4.7,-21 C 4.3,-17 3.4,-11 2.8,-6.4 C 2.4,-3.6 2.2,-1.6 2.5,-1.0 C 3.0,-0.2 4.2,-0.2 5.4,-1.0 C 6.8,-1.9 7.8,-3.6 7.6,-5.2 C 7.4,-6.6 6.2,-7.2 4.8,-6.6 C 3.8,-6.2 3.0,-5.2 2.6,-4.0 C 3.6,-4.8 5.4,-5.5 7.0,-5.5 C 7.9,-5.5 8.6,-5.4 9.0,-5.2"
    ]),
    "c": (7.6, [
        "M 0,0 C 1.2,-2.4 2.8,-6.2 4.4,-8.0 C 5.4,-9.0 6.6,-8.6 7.0,-7.2 C 6.6,-8.0 5.6,-8.0 4.6,-7.2 C 3.2,-6.0 2.2,-3.6 2.4,-2.2 C 2.6,-0.9 3.8,-0.5 5.2,-0.8 C 6.2,-1.0 7.0,-1.4 7.6,-1.8"
    ]),
    "d": (9.4, [
        "M 0,0 C 1.2,-2.4 2.8,-6.2 4.4,-8.0 C 5.4,-9.0 6.6,-8.6 6.9,-7.0 C 7.2,-5.4 6.6,-2.8 5.4,-1.4 C 4.2,-0.1 2.6,-0.5 2.1,-2.0 C 1.7,-3.4 2.4,-5.2 3.6,-6.2 C 4.6,-7.0 5.8,-7.2 6.6,-6.6 C 7.0,-10.4 7.6,-15.6 8.0,-18.4 C 8.2,-20.0 8.4,-20.8 8.4,-21.0 C 7.8,-16.6 7.2,-9.8 7.1,-5.0 C 7.1,-2.4 7.2,-1.0 7.6,-0.6 C 8.1,-0.1 8.8,-0.4 9.4,-1.0"
    ]),
    "e": (7.6, [
        "M 0,0 C 1.6,-1.6 3.6,-4.0 5.0,-5.8 C 5.8,-6.9 5.6,-8.0 4.4,-8.0 "
        "C 2.8,-8.0 1.2,-6.0 1.1,-3.8 C 1.0,-1.8 2.2,-0.6 3.8,-0.7 "
        "C 5.2,-0.8 6.6,-1.4 7.6,-0.4",
    ]),
    "f": (7.4, [
        "M 0,0 C 0.8,-3.4 1.8,-8.2 2.8,-12.8 C 3.6,-16.6 4.6,-20.2 5.6,-20.8 "
        "C 6.2,-21.2 6.4,-20.0 5.8,-17.4 C 5.0,-13.4 3.8,-7.6 3.0,-2.6 "
        "C 2.4,1.4 1.6,4.6 0.6,5.8 C -0.2,6.8 -0.9,6.0 -0.7,4.6 "
        "C -0.5,3.0 1.0,1.4 3.0,0.4 C 4.6,-0.4 6.2,-0.6 7.4,-0.4",
    ]),
    "g": (9.0, [
        "M 0,0 C 1.2,-2.4 2.8,-6.2 4.4,-8.0 C 5.4,-9.0 6.6,-8.6 6.9,-7.0 C 7.2,-5.4 6.6,-2.8 5.4,-1.4 C 4.2,-0.1 2.6,-0.5 2.1,-2.0 C 1.7,-3.4 2.4,-5.2 3.6,-6.2 C 4.6,-7.0 5.8,-7.2 6.6,-6.6 C 6.4,-3.4 5.8,0.8 5.0,3.6 C 4.2,6.2 3.0,7.0 2.0,6.4 C 1.2,5.9 1.0,4.8 1.8,3.8 C 2.8,2.5 5.0,1.5 7.0,0.9 C 8.0,0.6 8.6,0.35 9.0,0.0"
    ]),
    "h": (9.2, [
        "M 0,0 C 0.8,-4.0 2.0,-10.0 2.8,-14.6 C 3.3,-17.8 3.8,-20.4 4.1,-21 "
        "C 3.8,-17 3.0,-10.6 2.4,-6.0 C 2.1,-3.4 1.9,-1.4 2.0,-0.6 "
        "C 2.6,-3.6 3.6,-6.4 4.8,-7.6 C 5.8,-8.6 6.8,-8.2 7.0,-6.6 "
        "C 7.2,-5.0 6.8,-2.8 6.8,-1.6 C 6.8,-0.6 7.2,-0.2 7.8,-0.3 "
        "C 8.4,-0.4 8.8,-0.8 9.2,-1.4",
    ]),
    "i": (5.0, [
        "M 0,0 C 1.0,-2.0 2.0,-4.8 2.8,-6.8 C 3.2,-7.8 3.4,-8.3 3.4,-8.2 "
        "C 3.0,-6.0 2.6,-3.2 2.6,-1.6 C 2.6,-0.6 3.0,-0.2 3.6,-0.3 "
        "C 4.2,-0.4 4.7,-0.9 5.0,-1.4",
        "M 3.3,-11.8 C 3.7,-12.1 4.2,-11.9 4.1,-11.3",
    ]),
    "j": (5.4, [
        "M 0,0 C 1.0,-2.0 2.2,-4.8 3.0,-6.8 C 3.4,-7.8 3.6,-8.3 3.6,-8.2 "
        "C 3.2,-5.4 2.8,-1.6 2.4,1.6 C 2.0,4.6 1.2,6.4 0.0,6.6 "
        "C -0.9,6.7 -1.6,6.0 -1.6,5.0",
        "M 3.5,-11.8 C 3.9,-12.1 4.4,-11.9 4.3,-11.3",
    ]),
    "k": (8.6, [
        "M 0,0 C 0.8,-4.0 2.0,-10.0 2.8,-14.6 C 3.3,-17.8 3.8,-20.4 4.1,-21 "
        "C 3.8,-17 3.0,-10.6 2.4,-6.0 C 2.1,-3.4 1.9,-1.2 2.0,-0.4 "
        "C 3.4,-2.4 5.4,-4.8 6.8,-6.6 C 5.6,-5.2 4.2,-3.8 3.4,-3.2 "
        "C 4.4,-3.0 5.6,-2.2 6.4,-1.4 C 7.0,-0.8 7.8,-0.6 8.6,-1.2",
    ]),
    "l": (6.2, [
        "M 0,0 C 0.8,-4.0 2.0,-10.0 2.8,-14.6 C 3.3,-17.8 3.8,-20.4 4.1,-21 "
        "C 3.8,-17 3.0,-10.6 2.6,-6.0 C 2.3,-3.2 2.2,-1.4 2.6,-0.8 "
        "C 3.1,-0.1 4.0,-0.3 4.7,-0.8 C 5.3,-1.2 5.8,-1.8 6.2,-2.4",
    ]),
    "m": (12.8, [
        "M 0,0 C 0.6,-2.6 1.4,-5.4 2.0,-7.0 C 2.4,-8.0 2.6,-8.5 2.6,-8.2 "
        "C 2.2,-6.0 1.8,-3.2 1.8,-1.0 C 2.4,-3.6 3.4,-6.4 4.4,-7.4 "
        "C 5.2,-8.2 6.0,-7.8 6.0,-6.4 C 6.0,-5.0 5.6,-3.0 5.6,-1.2 "
        "C 6.2,-3.6 7.2,-6.4 8.2,-7.4 C 9.0,-8.2 9.8,-7.8 9.8,-6.4 "
        "C 9.8,-5.0 9.4,-2.8 9.4,-1.6 C 9.4,-0.6 9.8,-0.2 10.5,-0.3 "
        "C 11.3,-0.4 12.1,-1.0 12.8,-1.8",
    ]),
    "n": (9.6, [
        "M 0,0 C 0.6,-2.6 1.4,-5.4 2.0,-7.0 C 2.4,-8.0 2.6,-8.5 2.6,-8.2 "
        "C 2.2,-6.0 1.8,-3.2 1.8,-1.0 C 2.4,-3.6 3.6,-6.4 4.8,-7.4 "
        "C 5.7,-8.2 6.6,-7.8 6.6,-6.4 C 6.6,-5.0 6.2,-2.8 6.2,-1.6 "
        "C 6.2,-0.6 6.6,-0.2 7.3,-0.3 C 8.1,-0.4 8.9,-1.0 9.6,-1.8",
    ]),
    "o": (7.8, [
        "M 0,0 C 1.2,-2.4 2.8,-6.2 4.4,-8.0 C 5.4,-9.0 6.6,-8.6 7.0,-7.0 C 7.5,-5.0 6.8,-2.4 5.4,-1.2 C 4.0,-0.1 2.4,-0.6 1.9,-2.2 C 1.5,-3.6 2.1,-5.4 3.2,-6.4 C 4.0,-7.1 4.8,-7.4 5.6,-7.2 C 6.4,-7.0 7.2,-6.6 7.8,-6.2"
    ]),
    "p": (9.0, [
        "M 0,0 C 0.8,-2.6 1.8,-5.6 2.6,-7.2 C 3.0,-8.0 3.2,-8.5 3.2,-8.2 "
        "C 2.6,-4.4 1.8,0.6 1.2,3.6 C 0.8,5.4 0.4,6.4 0.2,6.8 "
        "C 0.8,3.4 1.6,-0.6 2.4,-3.4 C 3.2,-6.2 4.6,-7.8 5.8,-7.6 "
        "C 7.0,-7.4 7.6,-5.8 7.0,-4.0 C 6.4,-2.2 4.8,-1.0 3.4,-1.4 "
        "C 4.8,-1.2 6.4,-1.8 7.4,-2.6 C 7.6,-1.8 8.0,-1.0 9.0,-0.6",
    ]),
    "r": (7.6, [
        "M 0,0 C 1.0,-3.0 2.2,-6.4 2.9,-8.0 C 3.1,-8.6 3.3,-8.9 3.3,-8.4 C 3.2,-7.8 3.1,-7.2 3.0,-6.8 C 3.9,-7.6 5.0,-8.0 5.9,-7.6 C 6.5,-7.3 6.6,-6.6 6.4,-5.8 C 6.1,-4.2 5.8,-2.4 5.8,-1.4 C 5.8,-0.6 6.1,-0.3 6.6,-0.4 C 7.1,-0.5 7.4,-0.9 7.6,-1.3"
    ]),
    "s": (6.2, [
        "M 0,0 C 1.4,-1.4 2.8,-3.4 3.6,-5.2 C 4.2,-6.6 4.4,-7.8 3.8,-8.0 "
        "C 3.0,-8.3 1.8,-7.2 1.6,-5.6 C 1.4,-4.0 2.2,-2.8 3.2,-2.0 "
        "C 4.0,-1.4 4.4,-0.8 4.2,-0.4 C 4.0,0.0 3.2,0.1 2.6,-0.3 "
        "C 3.6,-0.1 5.2,-0.5 6.2,-1.0",
    ]),
    "t": (6.6, [
        "M 0,0 C 0.8,-3.0 2.0,-7.6 2.8,-11.2 C 3.3,-13.4 3.7,-15.2 3.9,-15.8 "
        "C 3.6,-12.6 3.0,-8.0 2.6,-4.6 C 2.3,-2.4 2.2,-1.0 2.6,-0.6 "
        "C 3.1,0.0 4.0,-0.2 4.8,-0.8 C 5.5,-1.3 6.1,-1.9 6.6,-2.4",
        "M 0.8,-8.2 C 2.2,-8.8 4.2,-9.0 5.4,-8.5",
    ]),
    "u": (8.8, [
        "M 0,0 C 0.8,-2.6 1.6,-5.4 2.2,-7.2 C 2.6,-8.2 2.8,-8.7 2.8,-8.4 "
        "C 2.4,-6.2 1.8,-3.6 1.8,-2.0 C 1.8,-0.8 2.4,-0.4 3.2,-0.8 "
        "C 4.2,-1.3 5.2,-3.4 6.0,-5.6 C 6.4,-6.8 6.8,-7.8 7.0,-8.4 "
        "C 6.6,-6.0 6.2,-3.2 6.2,-1.6 C 6.2,-0.6 6.6,-0.2 7.3,-0.3 "
        "C 8.0,-0.4 8.5,-1.0 8.8,-1.6",
    ]),
    "v": (10.2, [
        "M 0,0 C 1.6,-3.6 3.0,-7.2 4.0,-10.2 C 4.6,-7.0 5.2,-3.4 5.8,-0.3 C 6.8,-3.6 8.0,-7.2 8.8,-10.2 C 9.6,-9.2 9.0,-7.4 7.8,-7.2 C 8.6,-6.8 9.6,-7.0 10.2,-7.6"
    ]),
    "w": (14.5, [
        "M 0,0 C 1.6,-3.6 3.0,-7.2 4.0,-10.2 C 4.5,-7.0 5.1,-3.4 5.7,-0.4 C 6.6,-3.4 7.6,-6.6 8.4,-9.4 C 8.9,-6.4 9.5,-3.2 10.1,-0.4 C 11.1,-3.6 12.3,-7.2 13.1,-10.2 C 13.9,-9.2 13.3,-7.4 12.1,-7.2 C 12.9,-6.8 13.9,-7.0 14.5,-7.6"
    ]),
    "y": (9.0, [
        "M 0,0 C 0.8,-2.6 1.8,-5.6 2.6,-7.2 C 3.0,-8.0 3.2,-8.5 3.2,-8.2 "
        "C 3.0,-6.0 3.0,-3.2 3.6,-1.6 C 4.0,-0.6 4.8,-0.8 5.6,-2.2 "
        "C 6.4,-3.6 7.0,-6.0 7.4,-8.4 C 6.8,-4.4 6.0,0.4 5.2,3.4 "
        "C 4.4,6.2 3.2,7.2 2.0,6.6 C 1.2,6.2 1.0,5.2 1.6,4.2 "
        "C 2.4,2.8 4.4,1.6 6.4,0.9 C 7.4,0.55 8.4,0.3 9.0,0.0",
    ]),
    "'": (3.0, [
        "M 1.4,-15.0 C 1.9,-13.4 1.7,-12.0 1.0,-11.0",
    ]),
    "?": (7.2, [
        "M 0.6,-11.8 C 1.2,-14.4 3.8,-15.6 5.4,-14.4 C 7.1,-13.1 6.4,-10.6 4.8,-9.0 "
        "C 3.8,-8.0 3.2,-6.8 3.2,-5.2",
        "M 2.9,-2.8 C 3.1,-2.3 3.1,-2.0 3.0,-1.6",
    ]),
    ".": (3.4, [
        "M 1.2,-0.9 C 1.7,-1.1 2.2,-0.9 2.2,-0.3",
    ]),
    ",": (3.4, [
        "M 1.4,-0.7 C 1.8,0.5 1.6,1.7 0.8,2.7",
    ]),
    # --- capitals (cap height -15) ---
    "A": (12.4, [
        "M 0.6,-0.3 C 2.4,-5.4 4.4,-10.8 6.0,-15.2 C 7.8,-10.6 9.6,-5.2 11.2,-0.4",
        "M 2.6,-5.4 C 5.0,-5.8 7.6,-5.8 9.4,-5.4",
    ]),
    "B": (10.8, [
        "M 1.0,-0.3 C 1.2,-5.0 1.0,-10.6 1.2,-15.0",
        "M 1.2,-15.0 C 4.0,-15.4 7.4,-14.8 8.3,-12.8 C 9.1,-11.0 7.6,-9.0 5.4,-8.6 "
        "C 4.0,-8.35 2.6,-8.4 1.2,-8.4",
        "M 1.2,-8.4 C 4.4,-8.8 8.2,-8.2 9.2,-5.8 C 10.1,-3.6 8.4,-0.9 5.6,-0.5 "
        "C 4.0,-0.3 2.4,-0.3 1.0,-0.3",
    ]),
    "C": (12.0, [
        "M 11.0,-13.0 C 9.4,-15.3 5.6,-15.9 3.0,-14.0 C 0.6,-12.2 0.0,-8.0 1.0,-4.6 "
        "C 2.0,-1.2 5.0,0.5 7.8,-0.6 C 9.4,-1.2 10.6,-2.4 11.4,-3.8",
    ]),
    "D": (11.6, [
        "M 1.2,-15.0 C 1.4,-10 1.2,-4.6 1.0,-0.3",
        "M 1.2,-15.0 C 5.4,-15.4 9.4,-13.4 10.4,-9.4 C 11.4,-5.2 8.4,-0.8 4.0,-0.4 "
        "C 3.0,-0.3 1.8,-0.3 1.0,-0.3",
    ]),
    "E": (10.0, [
        "M 9.0,-15.0 C 6.0,-15.4 2.6,-15.2 0.8,-14.8",
        "M 0.8,-14.8 C 1.0,-10 0.8,-4.6 0.8,-0.4",
        "M 0.8,-8.2 C 3.0,-8.6 5.6,-8.6 7.4,-8.3",
        "M 0.8,-0.4 C 3.6,-0.8 6.8,-0.6 9.2,-0.2",
    ]),
    "F": (9.6, [
        "M 9.0,-15.0 C 6.0,-15.4 2.6,-15.2 0.8,-14.8",
        "M 0.8,-14.8 C 1.0,-10 0.8,-4.6 0.8,-0.4",
        "M 0.8,-8.2 C 3.0,-8.6 5.6,-8.6 7.4,-8.3",
    ]),
    "G": (12.6, [
        "M 11.0,-13.0 C 9.4,-15.3 5.6,-15.9 3.0,-14.0 C 0.6,-12.2 0.0,-8.0 1.0,-4.6 "
        "C 2.0,-1.2 5.0,0.5 7.8,-0.6 C 9.8,-1.4 11.0,-3.4 11.2,-6.2",
        "M 11.2,-6.4 C 9.8,-6.6 8.2,-6.6 7.0,-6.4",
    ]),
    "H": (11.4, [
        "M 0.8,-15.0 C 1.0,-10 0.8,-4.6 0.8,-0.3",
        "M 9.6,-15.2 C 9.8,-10 9.6,-4.6 9.4,-0.4",
        "M 0.8,-8.0 C 3.6,-8.4 7.0,-8.4 9.6,-8.0",
    ]),
    "I": (5.0, [
        "M 2.2,-15.2 C 2.6,-10 2.4,-4.6 2.2,-0.3",
    ]),
    "J": (9.4, [
        "M 2.0,-15.0 C 4.0,-15.2 6.4,-15.4 8.2,-15.4",
        "M 6.2,-15.2 C 6.4,-10 6.2,-4.6 5.6,-2.0 C 5.0,0.6 2.6,1.0 1.2,-0.4 "
        "C 0.6,-1.0 0.4,-1.8 0.4,-2.6",
    ]),
    "K": (11.4, [
        "M 1.0,-15.0 C 1.2,-10 1.0,-4.6 1.0,-0.3",
        "M 10.0,-15.2 C 7.4,-12.0 4.0,-9.0 1.4,-7.4",
        "M 4.2,-9.4 C 6.2,-6.6 8.4,-3.2 10.2,-0.4",
    ]),
    "L": (9.4, [
        "M 1.0,-15.0 C 1.2,-10 1.0,-4.6 1.0,-0.4",
        "M 1.0,-0.4 C 3.8,-0.8 6.8,-0.6 9.0,-0.2",
    ]),
    "M": (14.0, [
        "M 0.6,-0.3 C 0.8,-5.4 1.2,-10.6 1.6,-15.2",
        "M 1.6,-15.2 C 3.2,-11.4 5.2,-7.0 6.8,-4.0 C 8.4,-7.6 10.2,-11.8 11.8,-15.2",
        "M 11.8,-15.2 C 12.2,-10.6 12.6,-5.2 12.8,-0.3",
    ]),
    "N": (11.8, [
        "M 0.6,-0.3 C 0.8,-5.0 1.0,-10.4 1.2,-15.0",
        "M 1.2,-15.0 C 3.8,-10.6 6.8,-5.4 9.4,-1.0",
        "M 9.4,-1.0 C 9.6,-5.8 9.8,-10.6 10.0,-15.2",
    ]),
    "O": (13.0, [
        "M 6.6,-15.2 C 3.0,-15.2 0.5,-11.6 0.8,-7.4 C 1.0,-3.4 3.4,-0.3 6.6,-0.3 "
        "C 10.0,-0.3 12.4,-3.8 12.2,-8.0 C 12.0,-12.0 9.8,-15.2 6.6,-15.2 Z",
    ]),
    "P": (10.6, [
        "M 1.0,-0.3 C 1.2,-5.0 1.0,-10.6 1.2,-15.0",
        "M 1.2,-15.0 C 4.2,-15.4 8.0,-14.8 9.0,-12.4 C 9.9,-10.2 8.2,-7.8 5.6,-7.4 "
        "C 4.0,-7.2 2.6,-7.3 1.2,-7.3",
    ]),
    "R": (11.2, [
        "M 1.0,-0.3 C 1.2,-5.0 1.0,-10.6 1.2,-15.0",
        "M 1.2,-15.0 C 4.0,-15.4 7.6,-15.0 8.6,-13.0 C 9.5,-11.2 8.0,-9.0 5.6,-8.6 "
        "C 4.0,-8.35 2.6,-8.4 1.2,-8.4",
        "M 4.6,-8.6 C 6.4,-6.0 8.4,-3.0 10.4,-0.4",
    ]),
    "S": (10.4, [
        "M 9.0,-13.4 C 8.0,-15.1 5.0,-15.9 3.0,-14.6 C 1.2,-13.5 1.0,-11.0 2.8,-9.8 "
        "C 4.6,-8.6 7.4,-8.4 8.6,-6.8 C 9.8,-5.2 8.8,-2.2 6.4,-1.0 "
        "C 4.2,0.1 1.8,-0.4 0.6,-2.0",
    ]),
    "T": (10.4, [
        "M 0.4,-15.0 C 3.4,-15.4 7.0,-15.4 9.8,-15.0",
        "M 5.0,-15.2 C 5.2,-10 5.0,-4.6 4.8,-0.3",
    ]),
    "U": (11.6, [
        "M 0.8,-15.2 C 0.6,-10.6 0.4,-6.0 1.2,-3.4 C 2.2,-0.4 6.0,0.6 8.4,-1.2 "
        "C 9.8,-2.3 10.2,-4.6 10.3,-7.0 C 10.4,-9.8 10.4,-12.6 10.4,-15.2",
    ]),
    "V": (11.4, [
        "M 0.6,-15.0 C 1.8,-10 3.8,-4.6 5.6,-0.4 C 7.4,-5.0 9.2,-10.4 10.6,-15.2",
    ]),
    "W": (15.8, [
        "M 0.6,-15.0 C 1.4,-10.4 2.8,-5.0 4.2,-0.6 C 5.4,-4.8 6.6,-9.4 7.4,-13.0",
        "M 7.4,-13.0 C 8.4,-9.2 9.8,-4.6 11.0,-0.6 C 12.6,-5.2 14.0,-10.6 15.0,-15.2",
    ]),
    "X": (11.0, [
        "M 0.8,-15.0 C 3.4,-10.2 6.8,-4.8 9.8,-0.4",
        "M 10.0,-15.2 C 7.2,-10.4 3.8,-4.8 0.8,-0.4",
    ]),
    "Y": (11.0, [
        "M 0.6,-15.0 C 2.0,-11.6 4.0,-8.6 5.4,-7.0 C 7.0,-9.6 8.8,-12.6 10.2,-15.2",
        "M 5.4,-7.0 C 5.4,-4.6 5.2,-2.2 5.0,-0.3",
    ]),
    "Z": (10.4, [
        "M 0.8,-15.0 C 3.6,-15.4 7.0,-15.4 9.6,-15.0",
        "M 9.6,-15.0 C 7.0,-10.4 3.6,-4.6 0.8,-0.4",
        "M 0.8,-0.4 C 3.6,-0.8 7.0,-0.7 9.8,-0.3",
    ]),
    "0": (9.6, [
        "M 4.8,-15.2 C 2.4,-15.2 1.0,-11.8 1.2,-7.6 C 1.4,-3.6 3.0,-0.3 5.2,-0.3 "
        "C 7.6,-0.3 8.9,-3.8 8.7,-8.0 C 8.5,-12.0 7.0,-15.2 4.8,-15.2 Z",
    ]),
    "1": (6.6, [
        "M 1.0,-12.6 C 2.2,-13.6 3.4,-14.6 4.2,-15.2 C 4.4,-10.4 4.2,-4.8 4.0,-0.3",
    ]),
    "2": (9.6, [
        "M 1.0,-12.6 C 1.8,-14.8 4.4,-15.8 6.4,-15.0 C 8.4,-14.2 8.8,-11.4 7.4,-9.2 "
        "C 5.8,-6.6 2.6,-4.0 0.8,-0.4 C 3.6,-0.8 6.6,-0.7 9.0,-0.3",
    ]),
    "3": (9.2, [
        "M 1.0,-13.6 C 2.2,-15.4 5.0,-15.9 6.8,-14.8 C 8.4,-13.8 8.2,-11.2 6.2,-10.0 "
        "C 5.4,-9.5 4.4,-9.3 3.6,-9.3 C 5.4,-9.3 7.8,-8.6 8.4,-6.4 "
        "C 9.0,-4.0 7.4,-1.2 4.8,-0.5 C 2.8,0.0 1.2,-0.8 0.6,-2.2",
    ]),
    "4": (9.8, [
        "M 6.8,-15.2 C 4.6,-11.4 2.2,-7.4 0.6,-4.6 C 3.4,-4.8 6.4,-4.8 9.0,-4.6",
        "M 6.8,-15.2 C 6.6,-10.0 6.4,-4.6 6.2,-0.3",
    ]),
    "5": (9.4, [
        "M 8.2,-15.0 C 6.0,-15.3 3.4,-15.2 1.8,-15.0 C 1.6,-12.6 1.4,-10.6 1.2,-8.8 "
        "C 3.2,-9.8 6.0,-9.6 7.4,-8.0 C 9.0,-6.2 8.6,-2.8 6.2,-1.2 "
        "C 4.2,0.1 1.8,-0.4 0.6,-2.0",
    ]),
    "6": (9.4, [
        "M 8.0,-14.4 C 6.0,-15.8 3.2,-14.6 2.0,-11.4 C 1.0,-8.8 0.8,-5.4 1.4,-3.2 "
        "C 2.0,-1.0 3.8,-0.1 5.6,-0.4 C 7.6,-0.8 8.8,-2.8 8.4,-5.0 "
        "C 8.0,-7.2 5.8,-8.4 3.8,-7.8 C 2.4,-7.4 1.6,-6.2 1.3,-4.8",
    ]),
    "7": (9.2, [
        "M 0.8,-15.0 C 3.6,-15.4 6.8,-15.4 9.2,-15.0 C 7.2,-10.2 5.2,-4.8 4.2,-0.3",
    ]),
    "9": (9.4, [
        "M 8.0,-8.2 C 7.0,-6.4 4.8,-5.6 3.0,-6.4 C 1.2,-7.2 0.6,-9.6 1.6,-11.8 "
        "C 2.6,-14.0 5.0,-15.2 7.0,-14.4 C 8.6,-13.8 8.6,-11.6 8.4,-9.0 "
        "C 8.0,-5.0 7.2,-1.6 5.0,-0.4 C 3.6,0.3 2.2,0.0 1.4,-0.8",
    ]),
    "8": (9.6, [
        "M 5.0,-15.2 C 2.8,-15.2 1.4,-13.6 1.6,-11.8 C 1.8,-9.8 4.0,-8.8 5.8,-8.2 "
        "C 7.8,-7.6 9.0,-6.0 8.8,-4.0 C 8.6,-1.6 6.6,-0.2 4.4,-0.3 "
        "C 2.2,-0.4 0.6,-1.8 0.8,-4.0 C 1.0,-6.2 3.0,-7.6 5.0,-8.2 "
        "C 6.8,-8.8 7.8,-10.0 7.6,-11.8 C 7.4,-13.8 6.4,-15.2 5.0,-15.2 Z",
    ]),
}

NUM = re.compile(r"-?\d*\.?\d+(?:e-?\d+)?")
CMD = re.compile(r"([MLCZ])([^MLCZ]*)")


def _rng(seed):
    """Small deterministic pseudo-random source, so the hand never re-rolls."""
    state = (seed * 1103515245 + 12345) & 0x7FFFFFFF

    def nxt():
        nonlocal state
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return (state / 0x7FFFFFFF) * 2 - 1

    return nxt


def _points(subpath):
    out = []
    for cmd, args in CMD.findall(subpath):
        nums = [float(n) for n in NUM.findall(args)]
        out.append((cmd, [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]))
    return out


def _emit(parts):
    chunks = []
    for cmd, pts in parts:
        if cmd == "Z":
            chunks.append("Z")
        else:
            coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
            chunks.append(f"{cmd} {coords}")
    return " ".join(chunks)


def glyph_paths(char, seed, jitter=0.16, bounce=0.0, tilt=0.0, size=1.0):
    """Return one glyph's subpaths, shaken by hand, plus its advance width."""
    if char not in GLYPHS:
        raise KeyError(f"no glyph drawn for {char!r}")
    width, subpaths = GLYPHS[char]
    rnd = _rng(seed)
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)
    result = []
    for subpath in subpaths:
        parts = []
        for cmd, pts in _points(subpath):
            moved = []
            for x, y in pts:
                x += rnd() * jitter
                y += rnd() * jitter
                x, y = x * cos_t - y * sin_t, x * sin_t + y * cos_t
                moved.append((x * size, y * size + bounce))
            parts.append((cmd, moved))
        result.append(_emit(parts))
    return result, width * size


def _drift(x, seed=0, amount=0.9, wavelength=46.0):
    """A slow wander of the baseline. Continuous in x, so joins stay closed."""
    phase = (seed % 17) * 0.37
    return (math.sin(x / wavelength + phase) * amount
            + math.sin(x / (wavelength * 0.37) + phase * 2.1) * amount * 0.35)


def write(text, x=0.0, y=0.0, seed=1, tracking=None, size=1.0, jitter=0.16,
          bounce=0.5, slant=SLANT_DEG, connected=True, drift=0.9):
    """Lay out a line of handwriting. Returns (path strings, pen end x).

    Joined up, letters abut so the strokes run into each other and the whole
    line rides a drifting baseline. Set connected=False for print capitals,
    which get their own spacing, tilt and bounce instead.
    """
    if tracking is None:
        tracking = JOIN_SPACING if connected else LETTER_SPACING
    paths = []
    pen = x
    joinable = None
    tan = math.tan(math.radians(slant))
    for i, char in enumerate(text):
        if char == " ":
            pen += WORD_SPACING * size
            joinable = None
            continue
        rnd = _rng(seed * 97 + i * 31)
        if connected:
            dy, tilt, scale = 0.0, 0.0, size
        else:
            dy = rnd() * bounce
            tilt = math.radians(rnd() * 1.8)
            scale = size * (1 + rnd() * 0.09)
        subpaths, advance = glyph_paths(char, seed * 131 + i * 17, jitter=jitter,
                                        bounce=dy, tilt=tilt, size=scale)
        def place(pts):
            out = []
            for px, py in pts:
                gx = px + pen
                wave = _drift(gx, seed, drift * size) if connected else 0.0
                out.append((gx + (-py) * tan, py + y + wave))
            return out

        if connected and joinable and char not in DETACHED:
            # swing down from the last letter's high exit into this one
            ex, ey = joinable
            entry = place([(0.0, 0.0)])[0]
            dip = 0.5 if ey > -1 else 1.4
            paths.append(_emit([("M", [(ex, ey)]),
                                ("C", [(ex + 1.2, ey + dip),
                                       (entry[0] - 1.6, entry[1] - dip * 0.4),
                                       entry])]))
        for sp in subpaths:
            parts = [(cmd, place(pts)) for cmd, pts in _points(sp)]
            paths.append(_emit(parts))
        exit_y = EXIT_Y.get(char, 0.0) * scale
        joinable = (place([(advance, exit_y)])[0]
                    if connected and char not in DETACHED else None)
        pen += advance + tracking * size
    return paths, pen - tracking * size


def measure(text, tracking=None, size=1.0, connected=True):
    if tracking is None:
        tracking = JOIN_SPACING if connected else LETTER_SPACING
    pen = 0.0
    for char in text:
        if char == " ":
            pen += WORD_SPACING * size
            continue
        pen += GLYPHS[char][0] * size + tracking * size
    return pen - tracking * size


# --- hand-drawn shapes ------------------------------------------------------

def wobble_ellipse(cx, cy, rx, ry, seed=7, laps=1, wobble=0.9, rotate=0.0):
    """An ellipse drawn in one go, with the overshoot of a real pen."""
    rnd = _rng(seed)
    steps = 26
    start = -0.35
    total = laps * 2 * math.pi + 0.5
    pts = []
    for i in range(steps + 1):
        t = start + total * i / steps
        r_x = rx + rnd() * wobble
        r_y = ry + rnd() * wobble * 0.7
        px, py = math.cos(t) * r_x, math.sin(t) * r_y
        ca, sa = math.cos(rotate), math.sin(rotate)
        pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
    return _catmull(pts)


def wobble_line(x1, y1, x2, y2, seed=11, wobble=0.5, steps=8):
    rnd = _rng(seed)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((x1 + (x2 - x1) * t + rnd() * wobble * 0.4,
                    y1 + (y2 - y1) * t + rnd() * wobble))
    return _catmull(pts)


def wobble_pill(x, y, w, h, seed=5, wobble=1.2):
    """A hand-drawn pill: a rounded rectangle looped round in one stroke."""
    rnd = _rng(seed)
    r = h / 2
    pts = []
    steps = 44
    for i in range(steps + 1):
        t = i / steps
        # walk the perimeter: top edge, right cap, bottom edge, left cap
        straight = max(w - h, 1.0)
        perim = 2 * straight + 2 * math.pi * r
        d = t * (perim + straight * 0.035)  # the small overlap where the pen closes
        d = d % perim
        if d < straight:
            px, py = x + r + d, y
        elif d < straight + math.pi * r:
            a = (d - straight) / r - math.pi / 2
            px, py = x + r + straight + math.cos(a) * r, y + r + math.sin(a) * r
        elif d < 2 * straight + math.pi * r:
            px, py = x + r + straight - (d - straight - math.pi * r), y + h
        else:
            a = (d - 2 * straight - math.pi * r) / r + math.pi / 2
            px, py = x + r + math.cos(a) * r, y + r + math.sin(a) * r
        pts.append((px + rnd() * wobble * 0.5, py + rnd() * wobble * 0.5))
    return _catmull(pts)


def _catmull(pts):
    """Catmull-Rom through the points, emitted as cubic beziers."""
    if len(pts) < 2:
        return ""
    d = [f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"]
    ext = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C {c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} "
                 f"{p2[0]:.2f},{p2[1]:.2f}")
    return " ".join(d)


# --- the marks used on the site --------------------------------------------

def svg(view, body, klass, title, stroke=1.5):
    return (
        f'<svg class="{klass}" viewBox="{view}" fill="none" stroke="currentColor" '
        f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
        f'role="img" aria-label="{title}" focusable="false">\n'
        f'{body}\n</svg>'
    )


def paths_to_body(paths, indent="  ", extra=""):
    return "\n".join(f'{indent}<path{extra} d="{p}"/>' for p in paths)


def mark_pill():
    """The red marker ring around JOIN THE CONVERSATION.

    Drawn for a 400x56 box and stretched to whatever the button measures;
    the stroke stays even because it does not scale with the box.
    """
    d = wobble_pill(5, 5, 390, 46, seed=41, wobble=1.4)
    return ('<svg class="shape shape--pill" viewBox="0 0 400 56" fill="none" '
            'stroke="currentColor" stroke-width="4" stroke-linecap="round" '
            'stroke-linejoin="round" preserveAspectRatio="none" '
            'aria-hidden="true" focusable="false">\n'
            f'  <path vector-effect="non-scaling-stroke" d="{d}"/>\n</svg>')


def mark_ring():
    """The ring drawn round the date."""
    d = wobble_ellipse(110, 38, 103, 32, seed=61, wobble=1.1)
    return ('<svg class="shape shape--ring" viewBox="0 0 220 76" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" preserveAspectRatio="none" '
            'aria-hidden="true" focusable="false">\n'
            f'  <path vector-effect="non-scaling-stroke" d="{d}"/>\n</svg>')


def mark_close():
    a = wobble_line(2, 2, 18, 18, seed=81, wobble=0.5)
    b = wobble_line(18, 2, 2, 18, seed=82, wobble=0.5)
    body = f'  <path d="{a}"/>\n  <path d="{b}"/>'
    return svg("0 0 20 20", body, "mark mark--close", "close", stroke=1.7)


MARKS = {
    "pill": mark_pill,
    "ring": mark_ring,
    "close": mark_close,
}


def main():
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    rendered = {}
    for name, fn in MARKS.items():
        markup = fn()
        rendered[name] = markup
        standalone = markup.replace(
            "<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        (SVG_DIR / f"{name}.svg").write_text(standalone + "\n", encoding="utf-8")
        print(f"wrote assets/svg/{name}.svg")

    for page in sorted(ROOT.glob("*.html")):
        src = page.read_text(encoding="utf-8")
        out = src
        for name, markup in rendered.items():
            pattern = re.compile(
                rf"(<!-- hw:{name} -->)(.*?)(<!-- /hw:{name} -->)", re.S)

            def repl(m, markup=markup):
                indent = " " * 8
                inner = "\n".join(indent + line for line in markup.splitlines())
                return f"{m.group(1)}\n{inner}\n{indent}{m.group(3)}"

            out = pattern.sub(repl, out)
        if out != src:
            page.write_text(out, encoding="utf-8")
            print(f"updated {page.name}")


if __name__ == "__main__":
    main()
