#!/usr/bin/env python3
"""Draws VeltOS's "This PC" and Recycle Bin icons (branding/*.svg).

Original artwork in the look of Windows 11's icons (the product owner asked
for them to look the same; Microsoft's own files are copyrighted and are
not used): a monitor with a cyan-to-blue screen on a grey stand, and a
frosted glass bin with a grey foot and the blue recycling arrows (the
universal recycling symbol is in the public domain), empty and full of
crumpled paper.

    python3 tools/draw-icons.py        (rewrites branding/computer.svg,
                                        user-trash.svg, user-trash-full.svg)
"""

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "branding"
# Icon names of the terminal (Konsole's desktop entry uses utilities-terminal).
TERMINAL_NAMES = ("utilities-terminal", "org.kde.konsole", "konsole", "terminal")
HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">\n'
          '  <!-- {what}: VeltOS artwork in the look of Windows 11 (tools/draw-icons.py).\n'
          '       SPDX-License-Identifier: CC-BY-SA-4.0 -->\n')


def fmt(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


# --- This PC ---------------------------------------------------------------------

def computer():
    return HEADER.format(what='"This PC"') + """  <defs>
    <linearGradient id="screen" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#37D3E6"/>
      <stop offset="0.55" stop-color="#25AEE0"/>
      <stop offset="1" stop-color="#1A84D6"/>
    </linearGradient>
    <linearGradient id="sheen" x1="0" y1="0" x2="0.6" y2="1">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.22"/>
      <stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="bezel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#4F5560"/>
      <stop offset="1" stop-color="#2F333A"/>
    </linearGradient>
    <linearGradient id="neck" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#B9BDC4"/>
      <stop offset="0.5" stop-color="#DDE0E4"/>
      <stop offset="1" stop-color="#B3B7BE"/>
    </linearGradient>
    <linearGradient id="base" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#A7ACB3"/>
      <stop offset="1" stop-color="#6E747C"/>
    </linearGradient>
  </defs>
  <!-- stand -->
  <rect x="114" y="186" width="28" height="30" fill="url(#neck)"/>
  <rect x="114" y="186" width="28" height="6" fill="#000000" opacity="0.18"/>
  <rect x="80" y="212" width="96" height="12" rx="3" fill="url(#base)"/>
  <rect x="80" y="212" width="96" height="2.5" rx="1.25" fill="#FFFFFF" opacity="0.45"/>
  <!-- monitor -->
  <rect x="18" y="34" width="220" height="156" rx="9" fill="url(#bezel)"/>
  <rect x="24" y="40" width="208" height="144" rx="4" fill="url(#screen)"/>
  <rect x="24" y="40" width="208" height="144" rx="4" fill="url(#sheen)"/>
  <rect x="18.75" y="34.75" width="218.5" height="154.5" rx="8.5" fill="none"
        stroke="#FFFFFF" stroke-opacity="0.18" stroke-width="1.5"/>
</svg>
"""


# --- Recycle Bin -----------------------------------------------------------------

def recycle_arrows(cx, cy, radius, band):
    """Three bent arrows around a triangle (the recycling symbol), centred
    at (cx, cy): for each, the centre line of its band (drawn as a stroke
    with round joins) and its arrow head."""
    vertices = [(cx + radius * math.cos(math.radians(a)), cy + radius * math.sin(math.radians(a)))
                for a in (-90, 30, 150)]
    arrows = []
    for i in range(3):
        a, b, c = vertices[i], vertices[(i + 1) % 3], vertices[(i + 2) % 3]
        # From just past the middle of side a-b, round the corner at b, to
        # before the middle of side b-c, where the head points on.
        line = [lerp(a, b, 0.58), b, lerp(b, c, 0.22)]
        d = unit(sub(c, b))
        n = (-d[1], d[0])
        base = lerp(b, c, 0.20)
        head = [add(base, scale(n, band * 1.15)), lerp(b, c, 0.47), add(base, scale(n, -band * 1.15))]
        arrows.append((line, head))
    return arrows


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def scale(p, f):
    return (p[0] * f, p[1] * f)


def unit(p):
    length = math.hypot(*p)
    return (p[0] / length, p[1] / length)


BIN_DEFS = """  <defs>
    <linearGradient id="glass" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#C9DDF0" stop-opacity="0.95"/>
      <stop offset="0.3" stop-color="#EAF4FC" stop-opacity="0.82"/>
      <stop offset="0.7" stop-color="#DCEBF8" stop-opacity="0.82"/>
      <stop offset="1" stop-color="#B9D0E8" stop-opacity="0.95"/>
    </linearGradient>
    <linearGradient id="glassShade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#7F9DBD" stop-opacity="0.18"/>
    </linearGradient>
    <linearGradient id="rim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/>
      <stop offset="1" stop-color="#D3E3F2"/>
    </linearGradient>
    <linearGradient id="foot" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B8BCC2"/>
      <stop offset="1" stop-color="#8E949B"/>
    </linearGradient>
    <linearGradient id="arrow" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2E8BE6"/>
      <stop offset="1" stop-color="#0B5FB8"/>
    </linearGradient>
    <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/>
      <stop offset="1" stop-color="#E4E8EE"/>
    </linearGradient>
  </defs>
"""

# The bin: slightly narrower at the foot, glass walls, grey foot.
BODY = "M 34 46 L 222 46 L 208 222 L 48 222 Z"


def crumpled_paper(rng, count, area, sizes):
    """Crumpled sheets in area (x0, y0, x1, y1): irregular light polygons
    with a few creases."""
    parts = []
    for _ in range(count):
        cx, cy = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3])
        r = rng.uniform(*sizes)
        points = []
        for k in range(9):
            angle = 2 * math.pi * k / 9 + rng.uniform(-0.25, 0.25)
            radius = r * rng.uniform(0.65, 1.15)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        shade = rng.choice(["#FFFFFF", "#F6F8FB", "#EEF2F6", "#E6EBF1"])
        parts.append(f'<polygon points="{fmt(points)}" fill="{shade}" stroke="#C3CCD6" '
                     'stroke-width="1" stroke-linejoin="round"/>')
        for _crease in range(2):
            p, q = rng.sample(points, 2)
            parts.append(f'<path d="M {p[0]:.1f} {p[1]:.1f} L {cx:.1f} {cy:.1f} L {q[0]:.1f} {q[1]:.1f}" '
                         'fill="none" stroke="#C9D2DC" stroke-width="1.2"/>')
    return "\n  ".join(parts)


def recycle_bin(full):
    arrows = []
    for line, head in recycle_arrows(128, 140, 50, 16):
        points = " L ".join(f"{x:.1f} {y:.1f}" for x, y in line)
        arrows.append(f'<path d="M {points}" fill="none" stroke="url(#arrow)" stroke-width="16" '
                      'stroke-linejoin="round"/>')
        arrows.append(f'<polygon points="{fmt(head)}" fill="url(#arrow)" stroke="url(#arrow)" '
                      'stroke-width="2" stroke-linejoin="round"/>')
    paper = pile = ""
    if full:
        # Paper filling the bin, seen through the glass, and a pile above
        # the rim.
        rng = random.Random(2026_10_20)
        paper = ("  <g clip-path=\"url(#inside)\" opacity=\"0.92\">\n  "
                 + crumpled_paper(rng, 18, (50, 50, 206, 214), (22, 36)) + "\n  </g>\n")
        pile = "  " + crumpled_paper(rng, 7, (56, 24, 200, 44), (18, 30)) + "\n"
    what = "Recycle Bin (full)" if full else "Recycle Bin (empty)"
    return (HEADER.format(what=what) + BIN_DEFS
            + '  <clipPath id="inside"><path d="' + BODY + '"/></clipPath>\n'
            + '  <ellipse cx="128" cy="232" rx="84" ry="7" fill="#000000" opacity="0.10"/>\n'
            + f'  <path d="{BODY}" fill="url(#glass)"/>\n'
            + paper
            + f'  <path d="{BODY}" fill="url(#glassShade)"/>\n'
            + '  <path d="M 52 60 L 62 210" stroke="#FFFFFF" stroke-opacity="0.55" stroke-width="5" stroke-linecap="round"/>\n'
            + f'  <path d="{BODY}" fill="none" stroke="#9DB6CF" stroke-width="2" stroke-linejoin="round"/>\n'
            + pile
            + '  <rect x="30" y="40" width="196" height="12" rx="4" fill="url(#rim)" stroke="#A9C0D8" stroke-width="1.5"/>\n'
            + '  <path d="M 47 214 L 209 214 L 208 228 Q 208 232 204 232 L 52 232 Q 48 232 48 228 Z" fill="url(#foot)"/>\n'
            + '  <rect x="48" y="214" width="161" height="2.5" fill="#FFFFFF" opacity="0.5"/>\n'
            + "  " + "\n  ".join(arrows) + "\n"
            + "</svg>\n")


# --- Folders and the local disk -----------------------------------------------------

FOLDER_DEFS = """  <defs>
    <linearGradient id="back" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F7B52C"/>
      <stop offset="1" stop-color="#E8960C"/>
    </linearGradient>
    <linearGradient id="front" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFE07A"/>
      <stop offset="1" stop-color="#FFC53A"/>
    </linearGradient>
    <linearGradient id="blue" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4FB0F5"/>
      <stop offset="1" stop-color="#1A6DD6"/>
    </linearGradient>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#6CC4FA"/>
      <stop offset="1" stop-color="#2C86E0"/>
    </linearGradient>
    <linearGradient id="orange" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#FF8A3D"/>
      <stop offset="1" stop-color="#E35A0C"/>
    </linearGradient>
    <linearGradient id="purple" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#A487E0"/>
      <stop offset="1" stop-color="#6E4DB8"/>
    </linearGradient>
  </defs>
"""

FOLDER_BODY = """  <path d="M 18 58 Q 18 44 32 44 H 94 Q 103 44 109 51 L 119 62 H 224 Q 238 62 238 76 V 204 Q 238 218 224 218 H 32 Q 18 218 18 204 Z" fill="url(#back)"/>
  <path d="M 18 96 Q 18 84 30 84 H 226 Q 238 84 238 96 V 204 Q 238 218 224 218 H 32 Q 18 218 18 204 Z" fill="url(#front)"/>
  <path d="M 30 86 H 226" stroke="#FFFFFF" stroke-opacity="0.65" stroke-width="3" stroke-linecap="round"/>
"""

# Coloured marks on the front of the special folders (centre about 128, 152).
FOLDER_MARKS = {
    "folder": "",
    "user-desktop": """  <rect x="82" y="116" width="92" height="64" rx="7" fill="url(#blue)"/>
  <rect x="88" y="122" width="80" height="44" rx="3" fill="#FFFFFF" opacity="0.25"/>
  <rect x="112" y="180" width="32" height="8" rx="2" fill="#1A5DB8"/>
""",
    "folder-download": """  <path d="M 116 108 H 140 V 146 H 160 L 128 182 L 96 146 H 116 Z" fill="url(#blue)"/>
  <rect x="90" y="188" width="76" height="9" rx="4.5" fill="#1A6DD6"/>
""",
    "folder-documents": """  <path d="M 96 106 H 146 L 166 126 V 196 Q 166 202 160 202 H 96 Q 90 202 90 196 V 112 Q 90 106 96 106 Z" fill="#FFFFFF"/>
  <path d="M 146 106 V 126 H 166 Z" fill="#D9E2EC"/>
  <path d="M 102 140 H 154 M 102 156 H 154 M 102 172 H 140" stroke="#3A8EE6" stroke-width="7" stroke-linecap="round"/>
""",
    "folder-pictures": """  <rect x="80" y="112" width="96" height="76" rx="8" fill="#FFFFFF"/>
  <rect x="87" y="119" width="82" height="62" rx="4" fill="url(#sky)"/>
  <path d="M 87 172 L 112 146 L 130 164 L 146 150 L 169 172 V 177 Q 169 181 165 181 H 91 Q 87 181 87 177 Z" fill="#41B86B"/>
  <circle cx="150" cy="134" r="8" fill="#FFD54A"/>
""",
    "folder-music": """  <path d="M 112 120 L 162 108 V 172" fill="none" stroke="url(#orange)" stroke-width="10" stroke-linejoin="round"/>
  <path d="M 112 120 V 184" fill="none" stroke="url(#orange)" stroke-width="10"/>
  <ellipse cx="100" cy="186" rx="16" ry="12" fill="url(#orange)"/>
  <ellipse cx="150" cy="174" rx="16" ry="12" fill="url(#orange)"/>
""",
    "folder-videos": """  <rect x="80" y="114" width="96" height="72" rx="10" fill="url(#purple)"/>
  <path d="M 118 132 L 146 150 L 118 168 Z" fill="#FFFFFF"/>
""",
}


def folder(name):
    what = "Folder" if name == "folder" else f"Folder ({name})"
    return HEADER.format(what=what) + FOLDER_DEFS + FOLDER_BODY + FOLDER_MARKS[name] + "</svg>\n"


def local_disk():
    return HEADER.format(what="Local disk") + """  <defs>
    <linearGradient id="top" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F4F6F8"/>
      <stop offset="1" stop-color="#DDE2E8"/>
    </linearGradient>
    <linearGradient id="side" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B9C1CB"/>
      <stop offset="1" stop-color="#8E98A5"/>
    </linearGradient>
  </defs>
  <path d="M 30 116 L 62 62 H 194 L 226 116 Z" fill="url(#top)" stroke="#A9B2BD" stroke-width="3" stroke-linejoin="round"/>
  <rect x="30" y="116" width="196" height="80" rx="12" fill="url(#side)"/>
  <rect x="30" y="116" width="196" height="5" fill="#FFFFFF" opacity="0.5"/>
  <rect x="52" y="150" width="104" height="10" rx="5" fill="#5E6873"/>
  <circle cx="198" cy="155" r="9" fill="#36C26A"/>
</svg>
"""


# --- Terminal ------------------------------------------------------------------------
# A dark window with a grey tab strip, the prompt chevron and a cursor bar,
# in the look of Windows Terminal's icon (product owner's reference image).

def terminal():
    return HEADER.format(what="Terminal") + """  <defs>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#3B3D44"/>
      <stop offset="1" stop-color="#1D1E22"/>
    </linearGradient>
    <linearGradient id="strip" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#8A8E97"/>
      <stop offset="1" stop-color="#666A73"/>
    </linearGradient>
    <clipPath id="window"><rect x="22" y="38" width="212" height="180" rx="24"/></clipPath>
  </defs>
  <rect x="22" y="42" width="212" height="180" rx="24" fill="#000000" opacity="0.18"/>
  <rect x="22" y="38" width="212" height="180" rx="24" fill="url(#body)"/>
  <g clip-path="url(#window)">
    <rect x="22" y="38" width="212" height="44" fill="url(#strip)"/>
    <rect x="22" y="38" width="212" height="3" fill="#FFFFFF" opacity="0.35"/>
    <rect x="22" y="82" width="212" height="2" fill="#000000" opacity="0.35"/>
  </g>
  <rect x="23" y="39" width="210" height="178" rx="23" fill="none" stroke="#000000" stroke-opacity="0.35" stroke-width="2"/>
  <path d="M 66 120 L 104 150 L 66 180" fill="none" stroke="#FFFFFF" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="118" y="168" width="64" height="16" rx="8" fill="#FFFFFF"/>
</svg>
"""


# Windows drive (NTFS) in File Explorer: the local disk with a blue window
# mark on its top, the way Windows marks its own drive. The mark is a
# window (frame and title bar), not Microsoft's four-pane logo, which is a
# trademark and is not shipped by VeltOS.
WINDOWS_MARK = """  <g transform="translate(100 70)">
    <rect x="0" y="0" width="56" height="38" rx="5" fill="#2F7BE6" stroke="#1D5FC2" stroke-width="2"/>
    <rect x="0" y="0" width="56" height="10" rx="5" fill="#9CC8FF"/>
    <rect x="0" y="6" width="56" height="4" fill="#9CC8FF"/>
    <rect x="7" y="16" width="42" height="15" rx="2" fill="#FFFFFF" opacity="0.9"/>
  </g>
"""


def windows_disk():
    return local_disk().replace("</svg>\n", WINDOWS_MARK + "</svg>\n").replace(
        "<!-- Local disk:", "<!-- Windows drive:")


# --- Small sizes (16, 22, 24 px) ---------------------------------------------------
# Drawn on the 16 px grid with lines on whole pixels: the large drawings
# shrunk to 16 px turned into a grey dash (disk) and a cut-off box (bin)
# in File Explorer's navigation pane (VM test 2026-10-20).

SMALL_HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">\n'
                '  <!-- {what}, small sizes: VeltOS artwork in the look of Windows 11\n'
                '       (tools/draw-icons.py). SPDX-License-Identifier: CC-BY-SA-4.0 -->\n')


def small_disk():
    return SMALL_HEADER.format(what="Local disk") + """  <defs>
    <linearGradient id="side" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#C3CAD3"/>
      <stop offset="1" stop-color="#97A1AD"/>
    </linearGradient>
  </defs>
  <path d="M 1.5 7.5 L 3.5 4.5 H 12.5 L 14.5 7.5 Z" fill="#EEF1F4" stroke="#8F99A6" stroke-linejoin="round"/>
  <rect x="1.5" y="7.5" width="13" height="5" rx="1" fill="url(#side)" stroke="#7E8894"/>
  <rect x="3" y="9.5" width="6" height="1" fill="#55606B"/>
  <rect x="11" y="9" width="2" height="2" rx="1" fill="#2FBF62"/>
</svg>
"""


def small_bin(full):
    paper = ""
    if full:
        paper = """  <path d="M 4.5 4 L 5.5 0.5 L 9 1.5 L 8 4 Z" fill="#FFFFFF" stroke="#9AA9BA" stroke-width="0.8" stroke-linejoin="round"/>
  <path d="M 7.5 4 L 9.5 1 L 12 2.5 L 11 4 Z" fill="#DCEBFB" stroke="#9AA9BA" stroke-width="0.8" stroke-linejoin="round"/>
"""
    what = "Recycle Bin (full)" if full else "Recycle Bin (empty)"
    return SMALL_HEADER.format(what=what) + paper + """  <path d="M 3.5 4.5 H 12.5 L 11.6 14.5 H 4.4 Z" fill="#DCE9F6" stroke="#7D97B2" stroke-linejoin="round"/>
  <rect x="2.5" y="3.5" width="11" height="2" rx="0.8" fill="#FFFFFF" stroke="#7D97B2"/>
  <path d="M 8 7.2 L 10.3 11.2 H 5.7 Z" fill="none" stroke="#1F78D1" stroke-width="1.4" stroke-linejoin="round"/>
</svg>
"""


def small_windows_disk():
    return small_disk().replace("</svg>\n", """  <rect x="9.5" y="0.5" width="6" height="5" rx="1" fill="#2F7BE6" stroke="#1D5FC2"/>
  <rect x="10" y="1" width="5" height="1.2" fill="#9CC8FF"/>
</svg>
""")


def small_terminal():
    return SMALL_HEADER.format(what="Terminal") + """  <rect x="1" y="2" width="14" height="12" rx="2" fill="#26272C"/>
  <path d="M 3 2 H 13 A 2 2 0 0 1 15 4 V 5 H 1 V 4 A 2 2 0 0 1 3 2 Z" fill="#7C808A"/>
  <path d="M 3.5 7 L 6 9 L 3.5 11" fill="none" stroke="#FFFFFF" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="7" y="10.4" width="4" height="1.3" rx="0.6" fill="#FFFFFF"/>
</svg>
"""


# --- Close (menus, dialogs, tabs) -------------------------------------------------
# Windows 11 shows a thin monochrome cross where Fluent (like Breeze) has a
# red disc with a cross ("Close" in menus, dialog buttons, tab buttons).
# The colour follows the KDE colour scheme (current-color-scheme).

def close_glyph(colour):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">\n'
            '  <!-- Close: VeltOS artwork in the look of Windows 11 (tools/draw-icons.py).\n'
            '       SPDX-License-Identifier: CC-BY-SA-4.0 -->\n'
            '  <defs><style type="text/css" id="current-color-scheme">'
            f'.ColorScheme-Text {{ color:{colour}; }}</style></defs>\n'
            '  <path class="ColorScheme-Text" style="fill:none;stroke:currentColor;stroke-width:1.15;'
            'stroke-linecap:round" d="M 4.5 4.5 L 11.5 11.5 M 11.5 4.5 L 4.5 11.5"/>\n'
            '</svg>\n')


def main():
    (OUT / "computer.svg").write_text(computer(), encoding="utf-8", newline="\n")
    (OUT / "user-trash.svg").write_text(recycle_bin(False), encoding="utf-8", newline="\n")
    (OUT / "user-trash-full.svg").write_text(recycle_bin(True), encoding="utf-8", newline="\n")
    for name in FOLDER_MARKS:
        (OUT / f"{name}.svg").write_text(folder(name), encoding="utf-8", newline="\n")
    (OUT / "drive-harddisk.svg").write_text(local_disk(), encoding="utf-8", newline="\n")
    (OUT / "drive-harddisk-windows.svg").write_text(windows_disk(), encoding="utf-8", newline="\n")
    # The icon of folders as a file type.
    (OUT / "inode-directory.svg").write_text(folder("folder"), encoding="utf-8", newline="\n")
    for name in TERMINAL_NAMES:
        (OUT / f"{name}.svg").write_text(terminal(), encoding="utf-8", newline="\n")
    (OUT / "close.svg").write_text(close_glyph("#363636"), encoding="utf-8", newline="\n")
    (OUT / "close-dark.svg").write_text(close_glyph("#dedede"), encoding="utf-8", newline="\n")
    small = OUT / "small"
    small.mkdir(exist_ok=True)
    (small / "drive-harddisk.svg").write_text(small_disk(), encoding="utf-8", newline="\n")
    (small / "drive-harddisk-windows.svg").write_text(small_windows_disk(), encoding="utf-8", newline="\n")
    (small / "user-trash.svg").write_text(small_bin(False), encoding="utf-8", newline="\n")
    (small / "user-trash-full.svg").write_text(small_bin(True), encoding="utf-8", newline="\n")
    for name in TERMINAL_NAMES:
        (small / f"{name}.svg").write_text(small_terminal(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
