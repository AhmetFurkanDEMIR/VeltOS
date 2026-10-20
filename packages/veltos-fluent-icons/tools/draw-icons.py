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
  <path d="M 44 118 L 70 82 H 186 L 212 118 Z" fill="url(#top)" stroke="#A9B2BD" stroke-width="2" stroke-linejoin="round"/>
  <rect x="44" y="118" width="168" height="52" rx="8" fill="url(#side)"/>
  <rect x="44" y="118" width="168" height="4" fill="#FFFFFF" opacity="0.5"/>
  <rect x="60" y="140" width="92" height="6" rx="3" fill="#6E7884"/>
  <circle cx="190" cy="143" r="6" fill="#36C26A"/>
</svg>
"""


def main():
    (OUT / "computer.svg").write_text(computer(), encoding="utf-8", newline="\n")
    (OUT / "user-trash.svg").write_text(recycle_bin(False), encoding="utf-8", newline="\n")
    (OUT / "user-trash-full.svg").write_text(recycle_bin(True), encoding="utf-8", newline="\n")
    for name in FOLDER_MARKS:
        (OUT / f"{name}.svg").write_text(folder(name), encoding="utf-8", newline="\n")
    (OUT / "drive-harddisk.svg").write_text(local_disk(), encoding="utf-8", newline="\n")
    # The icon of folders as a file type.
    (OUT / "inode-directory.svg").write_text(folder("folder"), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
