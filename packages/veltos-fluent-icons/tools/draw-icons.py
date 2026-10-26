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
# Icon names of USB sticks (File Explorer, KDE).
USB_NAMES = ("drive-removable-media-usb", "drive-removable-media-usb-pendrive")
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
  <!-- monitor: a thin dark bezel around the screen, as on Windows 11 -->
  <rect x="16" y="30" width="224" height="160" rx="8" fill="url(#bezel)"/>
  <rect x="20" y="34" width="216" height="150" rx="4" fill="url(#screen)"/>
  <rect x="20" y="34" width="216" height="150" rx="4" fill="url(#sheen)"/>
  <rect x="16.75" y="30.75" width="222.5" height="158.5" rx="7.5" fill="none"
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

# The special folders are coloured like Windows 11's (the product owner's
# reference: Desktop blue, Downloads teal, Documents slate, Pictures blue,
# Music orange to pink, Videos purple; plain folders stay yellow), each
# with a white mark on the front. VeltOS drawings, not Microsoft's files.
# name -> (back top, back bottom, front top, front bottom)
FOLDER_COLOURS = {
    "folder": ("#F7B52C", "#E8960C", "#FFE07A", "#FFC53A"),
    "user-desktop": ("#1A73D9", "#1458B4", "#53BDF7", "#1F8BEA"),
    "folder-download": ("#0B8C78", "#086E5F", "#38D2B3", "#0FA88D"),
    "folder-documents": ("#5A7590", "#465E77", "#A9BED2", "#7896B2"),
    "folder-pictures": ("#1E66C8", "#174FA0", "#5CB6FA", "#2382E6"),
    "folder-music": ("#E0484F", "#BC3341", "#FFA14F", "#F2557C"),
    "folder-videos": ("#6640C2", "#50309E", "#A889F5", "#7A55DE"),
}

# White marks on the front (centre about 128, 152).
FOLDER_MARKS = {
    "folder": "",
    "user-desktop": """  <rect x="86" y="118" width="84" height="56" rx="7" fill="none" stroke="#FFFFFF" stroke-width="9"/>
  <path d="M 112 190 H 144" stroke="#FFFFFF" stroke-width="9" stroke-linecap="round"/>
""",
    "folder-download": """  <path d="M 128 110 V 168 M 102 144 L 128 170 L 154 144" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 98 192 H 158" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round"/>
""",
    "folder-documents": """  <path d="M 100 112 H 142 L 160 130 V 192 Q 160 198 154 198 H 100 Q 94 198 94 192 V 118 Q 94 112 100 112 Z" fill="#FFFFFF"/>
  <path d="M 106 144 H 148 M 106 160 H 148 M 106 176 H 134" stroke="#7896B2" stroke-width="7" stroke-linecap="round"/>
""",
    "folder-pictures": """  <circle cx="150" cy="128" r="11" fill="#FFFFFF"/>
  <path d="M 84 190 L 116 150 L 136 172 L 152 156 L 176 190 Z" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="6" stroke-linejoin="round"/>
""",
    "folder-music": """  <path d="M 118 180 V 118 L 162 110 V 168" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linejoin="round"/>
  <ellipse cx="106" cy="182" rx="16" ry="12.5" fill="#FFFFFF"/>
  <ellipse cx="150" cy="170" rx="16" ry="12.5" fill="#FFFFFF"/>
""",
    "folder-videos": """  <rect x="86" y="118" width="84" height="66" rx="12" fill="#FFFFFF"/>
  <path d="M 118 136 L 144 151 L 118 166 Z" fill="#7A55DE"/>
""",
}

FOLDER_SHAPE_BACK = ("M 18 58 Q 18 44 32 44 H 94 Q 103 44 109 51 L 119 62 H 224 Q 238 62 238 76 "
                     "V 204 Q 238 218 224 218 H 32 Q 18 218 18 204 Z")
FOLDER_SHAPE_FRONT = "M 18 96 Q 18 84 30 84 H 226 Q 238 84 238 96 V 204 Q 238 218 224 218 H 32 Q 18 218 18 204 Z"


def folder(name):
    what = "Folder" if name == "folder" else f"Folder ({name})"
    back_top, back_bottom, front_top, front_bottom = FOLDER_COLOURS[name]
    defs = f"""  <defs>
    <linearGradient id="back" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{back_top}"/>
      <stop offset="1" stop-color="{back_bottom}"/>
    </linearGradient>
    <linearGradient id="front" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="{front_top}"/>
      <stop offset="1" stop-color="{front_bottom}"/>
    </linearGradient>
  </defs>
"""
    body = (f'  <path d="{FOLDER_SHAPE_BACK}" fill="url(#back)"/>\n'
            f'  <path d="{FOLDER_SHAPE_FRONT}" fill="url(#front)"/>\n'
            '  <path d="M 30 86 H 226" stroke="#FFFFFF" stroke-opacity="0.55" stroke-width="3" stroke-linecap="round"/>\n')
    return HEADER.format(what=what) + defs + body + FOLDER_MARKS[name] + "</svg>\n"


# 16 px drawings of the coloured folders (navigation pane, lists): the same
# colours on a 16 px grid with bolder marks.
SMALL_HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">\n'
                '  <!-- {what}, 16 px: VeltOS artwork in the look of Windows 11 (tools/draw-icons.py).\n'
                '       SPDX-License-Identifier: CC-BY-SA-4.0 -->\n')
SMALL_MARKS = {
    "user-desktop": '  <rect x="5" y="7.6" width="6" height="3.6" rx="0.6" fill="none" stroke="#FFFFFF" stroke-width="1.1"/>\n',
    "folder-download": ('  <path d="M 8 6.8 V 10.4 M 6.4 8.9 L 8 10.5 L 9.6 8.9" fill="none" stroke="#FFFFFF" '
                        'stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>\n'
                        '  <path d="M 6 12 H 10" stroke="#FFFFFF" stroke-width="1.2" stroke-linecap="round"/>\n'),
    "folder-documents": '  <path d="M 5.6 8 H 10.4 M 5.6 9.8 H 10.4 M 5.6 11.6 H 8.8" stroke="#FFFFFF" stroke-width="1.1" stroke-linecap="round"/>\n',
    "folder-pictures": ('  <path d="M 4.8 12.2 L 7 9.4 L 8.4 10.9 L 9.4 9.9 L 11.2 12.2 Z" fill="#FFFFFF"/>\n'
                        '  <circle cx="9.9" cy="7.9" r="0.9" fill="#FFFFFF"/>\n'),
    "folder-music": ('  <path d="M 7.2 11.6 V 7.6 L 10 7.1 V 10.8" fill="none" stroke="#FFFFFF" stroke-width="1"/>\n'
                     '  <circle cx="6.5" cy="11.7" r="1.1" fill="#FFFFFF"/><circle cx="9.3" cy="10.9" r="1.1" fill="#FFFFFF"/>\n'),
    "folder-videos": ('  <rect x="5" y="7.4" width="6" height="4.6" rx="1" fill="#FFFFFF"/>\n'
                      '  <path d="M 7.3 8.6 L 9.1 9.7 L 7.3 10.8 Z" fill="#7A55DE"/>\n'),
}


def small_folder(name):
    back_top, back_bottom, front_top, front_bottom = FOLDER_COLOURS[name]
    return (SMALL_HEADER.format(what=f"Folder ({name})")
            + f"""  <defs>
    <linearGradient id="back" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{back_top}"/><stop offset="1" stop-color="{back_bottom}"/>
    </linearGradient>
    <linearGradient id="front" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="{front_top}"/><stop offset="1" stop-color="{front_bottom}"/>
    </linearGradient>
  </defs>
  <path d="M 1.5 3.6 Q 1.5 2.5 2.6 2.5 H 5.9 Q 6.4 2.5 6.8 2.9 L 7.5 3.6 H 13.4 Q 14.5 3.6 14.5 4.7 V 12.4 Q 14.5 13.5 13.4 13.5 H 2.6 Q 1.5 13.5 1.5 12.4 Z" fill="url(#back)"/>
  <path d="M 1.5 6.1 Q 1.5 5.2 2.4 5.2 H 13.6 Q 14.5 5.2 14.5 6.1 V 12.4 Q 14.5 13.5 13.4 13.5 H 2.6 Q 1.5 13.5 1.5 12.4 Z" fill="url(#front)"/>
"""
            + SMALL_MARKS[name] + "</svg>\n")


# File Explorer's "Home": an orange house like Windows 11's (VeltOS name
# "veltos-home", so other programs keep their own home icons).
def home():
    return HEADER.format(what="File Explorer Home") + """  <defs>
    <linearGradient id="wall" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0" stop-color="#FFB45A"/>
      <stop offset="1" stop-color="#F57C1F"/>
    </linearGradient>
    <linearGradient id="roof" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#E8661A"/>
      <stop offset="1" stop-color="#C94E10"/>
    </linearGradient>
  </defs>
  <path d="M 54 116 L 128 56 L 202 116 V 212 Q 202 224 190 224 H 66 Q 54 224 54 212 Z" fill="url(#wall)"/>
  <path d="M 26 122 L 128 38 L 230 122" fill="none" stroke="url(#roof)" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 106 224 V 172 Q 106 160 118 160 H 138 Q 150 160 150 172 V 224 Z" fill="#FFFFFF" opacity="0.92"/>
</svg>
"""


def small_home():
    return SMALL_HEADER.format(what="File Explorer Home") + """  <path d="M 3.5 7.4 L 8 3.6 L 12.5 7.4 V 13 Q 12.5 13.8 11.7 13.8 H 4.3 Q 3.5 13.8 3.5 13 Z" fill="#FB9A3C"/>
  <path d="M 1.8 7.6 L 8 2.4 L 14.2 7.6" fill="none" stroke="#D9581A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 6.7 13.8 V 10.6 Q 6.7 10 7.3 10 H 8.7 Q 9.3 10 9.3 10.6 V 13.8 Z" fill="#FFFFFF"/>
</svg>
"""


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
  <g transform="translate(128 129) scale(1.17) translate(-128 -129)">
  <path d="M 30 116 L 62 62 H 194 L 226 116 Z" fill="url(#top)" stroke="#A9B2BD" stroke-width="3" stroke-linejoin="round"/>
  <rect x="30" y="116" width="196" height="80" rx="12" fill="url(#side)"/>
  <rect x="30" y="116" width="196" height="5" fill="#FFFFFF" opacity="0.5"/>
  <rect x="52" y="150" width="104" height="10" rx="5" fill="#5E6873"/>
  <circle cx="198" cy="155" r="9" fill="#36C26A"/>
  </g>
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
# A Windows drive: the local disk with a window on its front, in Windows
# 11's blue (product owner, 2026-10-23: "Windows 11's icon on NTFS drives").
# A framed window with a cross of glazing bars, not Microsoft's four-pane
# logo, which is a trademark VeltOS does not ship.
WINDOWS_MARK = """  <defs>
    <linearGradient id="pane" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4CC2FF"/>
      <stop offset="1" stop-color="#0F6CD8"/>
    </linearGradient>
  </defs>
  <g transform="translate(46 130)">
    <rect x="0" y="0" width="48" height="48" rx="7" fill="#0B4FB0"/>
    <rect x="4" y="4" width="40" height="40" rx="4" fill="url(#pane)"/>
    <rect x="22.5" y="4" width="3" height="40" fill="#FFFFFF" opacity="0.9"/>
    <rect x="4" y="22.5" width="40" height="3" fill="#FFFFFF" opacity="0.9"/>
    <path d="M 6 6 H 21 L 6 19 Z" fill="#FFFFFF" opacity="0.25"/>
  </g>
"""


def windows_disk():
    # The window takes the place of the slot's left part.
    return local_disk().replace(
        '<rect x="52" y="150" width="104" height="10" rx="5" fill="#5E6873"/>',
        '<rect x="110" y="150" width="68" height="10" rx="5" fill="#5E6873"/>').replace(
        "  </g>\n</svg>\n", WINDOWS_MARK + "  </g>\n</svg>\n").replace("<!-- Local disk:", "<!-- Windows drive:")


def removable_disk():
    return HEADER.format(what="Removable disk") + """  <defs>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F4F6F8"/>
      <stop offset="1" stop-color="#DDE2E8"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B9C1CB"/>
      <stop offset="1" stop-color="#8E98A5"/>
    </linearGradient>
    <linearGradient id="platter" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/>
      <stop offset="1" stop-color="#D8DEE5"/>
    </linearGradient>
  </defs>
  <g transform="translate(128 128) rotate(-7) translate(-128 -128)">
    <rect x="55" y="33" width="146" height="190" rx="24" fill="#65707C" opacity="0.3"/>
    <rect x="49" y="27" width="146" height="190" rx="24" fill="url(#edge)" stroke="#89939F" stroke-width="3"/>
    <rect x="56" y="34" width="132" height="174" rx="19" fill="url(#body)"/>
    <rect x="69" y="48" width="106" height="119" rx="16" fill="#F8FAFC" stroke="#BCC4CD" stroke-width="3"/>
    <circle cx="122" cy="106" r="36" fill="url(#platter)" stroke="#A7B1BC" stroke-width="3"/>
    <circle cx="122" cy="106" r="23" fill="none" stroke="#C2CAD2" stroke-width="2"/>
    <circle cx="122" cy="106" r="7" fill="#7B8794"/>
    <path d="M 126 108 L 150 137 L 137 143 L 122 109" fill="#7B8794"/>
    <rect x="94" y="181" width="38" height="9" rx="4.5" fill="#68727E"/>
    <circle cx="161" cy="185.5" r="6" fill="#2FA8F0"/>
    <circle cx="161" cy="185.5" r="2.5" fill="#FFFFFF" opacity="0.6"/>
  </g>
</svg>
"""


# A USB flash drive in the disk's family (product owner, 2026-10-23: "make
# the flash drive icon nicer, like Windows 11"): a light grey stick seen
# slightly from above with a metal USB plug and a blue light.
def usb_drive():
    return HEADER.format(what="USB drive") + """  <defs>
    <linearGradient id="top" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F4F6F8"/>
      <stop offset="1" stop-color="#DDE2E8"/>
    </linearGradient>
    <linearGradient id="side" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B9C1CB"/>
      <stop offset="1" stop-color="#8E98A5"/>
    </linearGradient>
    <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#E9ECEF"/>
      <stop offset="0.5" stop-color="#C5CBD2"/>
      <stop offset="1" stop-color="#9AA3AD"/>
    </linearGradient>
    <linearGradient id="metalTop" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FAFBFC"/>
      <stop offset="1" stop-color="#D9DEE3"/>
    </linearGradient>
  </defs>
  <g transform="translate(128 128) scale(1.12) translate(-128 -128) translate(0 -22)">
    <!-- the plug -->
    <path d="M 24 148 L 30 134 H 88 V 148 Z" fill="url(#metalTop)" stroke="#9EA7B1" stroke-width="2" stroke-linejoin="round"/>
    <rect x="24" y="148" width="64" height="32" rx="3" fill="url(#metal)" stroke="#8C96A1" stroke-width="2"/>
    <rect x="40" y="137" width="11" height="7" rx="1.5" fill="#5E6873"/>
    <rect x="61" y="137" width="11" height="7" rx="1.5" fill="#5E6873"/>
    <rect x="30" y="157" width="52" height="4" rx="2" fill="#FFFFFF" opacity="0.6"/>
    <!-- the stick -->
    <path d="M 80 136 L 94 114 H 218 L 232 136 Z" fill="url(#top)" stroke="#A9B2BD" stroke-width="3" stroke-linejoin="round"/>
    <rect x="80" y="136" width="152" height="56" rx="12" fill="url(#side)"/>
    <rect x="80" y="136" width="152" height="5" fill="#FFFFFF" opacity="0.5"/>
    <rect x="80" y="136" width="18" height="56" rx="6" fill="#7D8794" opacity="0.55"/>
    <rect x="114" y="160" width="64" height="9" rx="4.5" fill="#5E6873"/>
    <circle cx="207" cy="164.5" r="9" fill="#2FA8F0"/>
    <circle cx="207" cy="164.5" r="4" fill="#FFFFFF" opacity="0.55"/>
  </g>
</svg>
"""


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
    return small_disk().replace('<rect x="3" y="9.5" width="6" height="1" fill="#55606B"/>', """  <rect x="2.5" y="8" width="4" height="4" rx="0.8" fill="#1C78E6" stroke="#0B4FB0" stroke-width="0.8"/>
  <path d="M 4.5 8.4 V 11.6 M 2.9 10 H 6.1" stroke="#FFFFFF" stroke-width="0.7"/>""").replace(
        "<!-- Local disk", "<!-- Windows drive")


def small_removable_disk():
    return SMALL_HEADER.format(what="Removable disk") + """  <defs>
    <linearGradient id="case" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F4F6F8"/>
      <stop offset="1" stop-color="#C8D0D9"/>
    </linearGradient>
  </defs>
  <rect x="3" y="1.5" width="10" height="13" rx="2" fill="url(#case)" stroke="#7E8894"/>
  <rect x="4.5" y="3" width="7" height="7.5" rx="1" fill="#EEF1F4" stroke="#A3ADB8" stroke-width="0.7"/>
  <circle cx="8" cy="6.8" r="2.1" fill="#D6DDE4" stroke="#8994A0" stroke-width="0.7"/>
  <circle cx="8" cy="6.8" r="0.7" fill="#68727E"/>
  <rect x="6.2" y="11.5" width="3.6" height="0.8" rx="0.4" fill="#68727E"/>
  <circle cx="11.2" cy="12.3" r="0.8" fill="#2FA8F0"/>
</svg>
"""


def small_usb_drive():
    return SMALL_HEADER.format(what="USB drive") + """  <defs>
    <linearGradient id="side" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#C3CAD3"/>
      <stop offset="1" stop-color="#97A1AD"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="6.5" width="5" height="4" rx="0.6" fill="#DDE1E6" stroke="#8F99A6"/>
  <rect x="1.5" y="7.5" width="1" height="1" fill="#5E6873"/>
  <rect x="3.5" y="7.5" width="1" height="1" fill="#5E6873"/>
  <rect x="4.5" y="4.5" width="11" height="8" rx="1.5" fill="url(#side)" stroke="#7E8894"/>
  <rect x="4.5" y="4.5" width="11" height="2.5" rx="1.2" fill="#EEF1F4"/>
  <circle cx="12.5" cy="9.5" r="1.2" fill="#2FA8F0"/>
</svg>
"""


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
    (OUT / "veltos-home.svg").write_text(home(), encoding="utf-8", newline="\n")
    (OUT / "drive-harddisk.svg").write_text(local_disk(), encoding="utf-8", newline="\n")
    (OUT / "drive-harddisk-windows.svg").write_text(windows_disk(), encoding="utf-8", newline="\n")
    (OUT / "drive-removable-media.svg").write_text(removable_disk(), encoding="utf-8", newline="\n")
    for name in USB_NAMES:
        (OUT / f"{name}.svg").write_text(usb_drive(), encoding="utf-8", newline="\n")
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
    (small / "drive-removable-media.svg").write_text(small_removable_disk(), encoding="utf-8", newline="\n")
    for name in USB_NAMES:
        (small / f"{name}.svg").write_text(small_usb_drive(), encoding="utf-8", newline="\n")
    (small / "user-trash.svg").write_text(small_bin(False), encoding="utf-8", newline="\n")
    for name in SMALL_MARKS:
        (small / f"{name}.svg").write_text(small_folder(name), encoding="utf-8", newline="\n")
    (small / "veltos-home.svg").write_text(small_home(), encoding="utf-8", newline="\n")
    (small / "user-trash-full.svg").write_text(small_bin(True), encoding="utf-8", newline="\n")
    for name in TERMINAL_NAMES:
        (small / f"{name}.svg").write_text(small_terminal(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
