#!/usr/bin/env python3
"""Draws the VeltOS app icons (branding/apps/*.svg) as one family.

The product owner asked for the default apps' icons to look like Windows
11's and to match each other. These are original VeltOS drawings in the
look of Windows 11's app icons (Fluent style: objects rather than tiles,
soft top-to-bottom gradients, light from the top left, a faint contact
shadow, the same corner radii); Microsoft's own files and logos are not
used (the Store bag carries the VeltOS "V", not Microsoft's logo).

    python3 tools/app-icons.py         (rewrites branding/apps/*.svg)

Each drawing is installed under several icon names (NAMES below): the
VeltOS apps' own names and the names of the KDE/Debian apps they stand
for, so the Start menu, the taskbar and File Explorer show one family.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "branding" / "apps"

HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">\n'
          '  <!-- {what}: VeltOS artwork in the look of Windows 11 (tools/app-icons.py).\n'
          '       SPDX-License-Identifier: CC-BY-SA-4.0 -->\n')


def grad(gid, top, bottom, x2="0", y2="1", x1="0", y1="0"):
    return (f'    <linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">\n'
            f'      <stop offset="0" stop-color="{top}"/>\n'
            f'      <stop offset="1" stop-color="{bottom}"/>\n'
            f'    </linearGradient>\n')


def shadow(d):
    """Faint contact shadow under a shape (same for every icon)."""
    return f'  <path d="{d}" fill="#000000" opacity="0.16" transform="translate(0 5)"/>\n'


def rrect(x, y, w, h, r):
    return (f"M {x + r} {y} H {x + w - r} Q {x + w} {y} {x + w} {y + r} V {y + h - r} "
            f"Q {x + w} {y + h} {x + w - r} {y + h} H {x + r} Q {x} {y + h} {x} {y + h - r} "
            f"V {y + r} Q {x} {y} {x + r} {y} Z")


def svg(what, defs, body):
    return HEADER.format(what=what) + "  <defs>\n" + defs + "  </defs>\n" + body + "</svg>\n"


# --- the drawings ------------------------------------------------------------------------------

def calculator():
    body_d = rrect(52, 20, 152, 216, 18)
    keys = []
    for row in range(4):
        for col in range(3):
            x, y = 70 + col * 34, 104 + row * 32
            keys.append(f'  <rect x="{x}" y="{y}" width="26" height="24" rx="5" fill="url(#key)"/>\n')
    return svg("Calculator", grad("body", "#6B7686", "#465160") + grad("screen", "#7BE6FF", "#38B6F2")
               + grad("key", "#F2F4F7", "#D3D9E1") + grad("accent", "#4F7CFF", "#2B45C8"),
               shadow(body_d)
               + f'  <path d="{body_d}" fill="url(#body)"/>\n'
               + '  <path d="M 70 22 H 186" stroke="#FFFFFF" stroke-opacity="0.25" stroke-width="3" stroke-linecap="round"/>\n'
               + '  <rect x="70" y="40" width="116" height="48" rx="8" fill="url(#screen)"/>\n'
               + "".join(keys[:11])
               + '  <rect x="138" y="168" width="26" height="56" rx="5" fill="url(#accent)"/>\n')


def camera():
    # A wide camera body (about 3:2, like Windows 11's Camera icon) with a
    # large lens; the first drawing was nearly square and looked squeezed
    # next to the other icons (product owner, 2026-10-22).
    body_d = ("M 22 92 Q 22 72 42 72 H 76 L 92 50 Q 98 42 108 42 H 148 Q 158 42 164 50 L 180 72 "
              "H 214 Q 234 72 234 92 V 194 Q 234 214 214 214 H 42 Q 22 214 22 194 Z")
    return svg("Camera", grad("body", "#7B8594", "#4E5866") + grad("lens", "#C38BFF", "#3FA8F6", "1", "1")
               + grad("ring", "#FFFFFF", "#DCE2EA"),
               shadow(body_d)
               + '  <rect x="38" y="58" width="34" height="18" rx="6" fill="#2FA8F0"/>\n'
               + f'  <path d="{body_d}" fill="url(#body)"/>\n'
               + '  <path d="M 42 75 H 214" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="3" stroke-linecap="round"/>\n'
               + '  <circle cx="128" cy="142" r="60" fill="url(#ring)"/>\n'
               + '  <circle cx="128" cy="142" r="46" fill="url(#lens)"/>\n'
               + '  <circle cx="128" cy="142" r="20" fill="#1E2A44" opacity="0.35"/>\n'
               + '  <ellipse cx="110" cy="124" rx="15" ry="10" fill="#FFFFFF" opacity="0.38"/>\n'
               + '  <circle cx="206" cy="98" r="8" fill="#DDE3EA"/>\n')


def mail():
    """VeltOS Mail like the new Outlook's Windows 11 icon (product owner,
    2026-10-24, with a picture of it): a big, open envelope in blue to
    violet gradients with the letter inside and its lid folded back, and a
    small dark blue tile with a white O at the bottom left. A VeltOS drawing;
    Microsoft's icon files are not used."""
    body = "M 60 104 L 148 46 Q 156 41 164 46 L 244 98 V 196 Q 244 222 218 222 H 86 Q 60 222 60 196 Z"
    tile = rrect(14, 128, 104, 104, 22)
    return svg("Mail", grad("back", "#5B8DF7", "#2E5AD8") + grad("lid", "#A9C8FF", "#6C8EF5")
               + grad("paper", "#FFFFFF", "#DCEBFF") + grad("front", "#36A3F7", "#1B5FD6", x2="0.4", y2="1")
               + grad("right", "#4FC3F7", "#2A7DE8", x1="1", y1="0", x2="0", y2="1")
               + grad("tile", "#1677DB", "#0A3F96", x2="1", y2="1"),
               shadow(body)
               # The back of the envelope and its lid, folded back (light).
               + f'  <path d="{body}" fill="url(#back)"/>\n'
               + '  <path d="M 60 104 L 148 46 Q 156 41 164 46 L 244 98 L 152 120 Z" fill="url(#lid)" opacity="0.95"/>\n'
               # The letter inside.
               + '  <path d="M 84 92 Q 84 80 96 80 H 208 Q 220 80 220 92 V 170 H 84 Z" fill="url(#paper)"/>\n'
               + '  <path d="M 104 104 H 176 M 104 124 H 196" stroke="#9DBCEB" stroke-width="7" stroke-linecap="round"/>\n'
               # The front: two flaps meeting in the middle, the right one lighter.
               + '  <path d="M 60 118 L 152 176 L 152 222 H 86 Q 60 222 60 196 Z" fill="url(#front)"/>\n'
               + '  <path d="M 244 112 L 152 176 L 152 222 H 218 Q 244 222 244 196 Z" fill="url(#right)"/>\n'
               + '  <path d="M 60 118 L 152 176 L 244 112" fill="none" stroke="#FFFFFF" stroke-opacity="0.35" '
                 'stroke-width="3" stroke-linejoin="round"/>\n'
               # The O tile.
               + shadow(tile)
               + f'  <path d="{tile}" fill="url(#tile)"/>\n'
               + '  <path d="M 14 150 Q 14 128 36 128 H 96 Q 118 128 118 150 V 158 H 14 Z" fill="#FFFFFF" opacity="0.08"/>\n'
               + '  <ellipse cx="66" cy="180" rx="21" ry="25" fill="none" stroke="#FFFFFF" stroke-width="12"/>\n')


def snipping_tool():
    tile_d = rrect(28, 28, 168, 168, 26)
    return svg("Snipping Tool", grad("tile", "#F7F9FC", "#E3E8EF") + grad("blade", "#9AA4B2", "#6E7887")
               + grad("handle", "#5FC2FF", "#2F7BE6"),
               shadow(tile_d)
               + f'  <path d="{tile_d}" fill="url(#tile)" stroke="#D4DAE3" stroke-width="2"/>\n'
               + '  <path d="M 56 132 V 66 Q 56 56 66 56 H 132" fill="none" stroke="#F04A3C" stroke-width="14" '
                 'stroke-linecap="round" stroke-dasharray="22 16"/>\n'
               + '  <path d="M 112 112 L 200 200" stroke="url(#blade)" stroke-width="16" stroke-linecap="round"/>\n'
               + '  <path d="M 196 112 L 112 196" stroke="url(#blade)" stroke-width="16" stroke-linecap="round"/>\n'
               + '  <circle cx="102" cy="208" r="20" fill="none" stroke="url(#handle)" stroke-width="12"/>\n'
               + '  <circle cx="210" cy="208" r="20" fill="none" stroke="url(#handle)" stroke-width="12"/>\n'
               + '  <circle cx="155" cy="155" r="6" fill="#4A5361"/>\n')


def store():
    bag_d = "M 40 84 Q 40 72 52 72 H 204 Q 216 72 216 84 L 222 210 Q 222 226 206 226 H 50 Q 34 226 34 210 Z"
    return svg("VeltOS Store", grad("bag", "#3A6FE8", "#1D3FA6") + grad("v", "#FFFFFF", "#DCE6FF"),
               shadow(bag_d)
               + '  <path d="M 88 92 V 64 Q 88 34 128 34 Q 168 34 168 64 V 92" fill="none" stroke="#38C5F9" '
                 'stroke-width="14" stroke-linecap="round"/>\n'
               + f'  <path d="{bag_d}" fill="url(#bag)"/>\n'
               + '  <path d="M 52 75 H 204" stroke="#FFFFFF" stroke-opacity="0.25" stroke-width="3" stroke-linecap="round"/>\n'
               + '  <path d="M 92 112 L 128 192 L 164 112" fill="none" stroke="url(#v)" stroke-width="22" '
                 'stroke-linecap="round" stroke-linejoin="round"/>\n')


def app_installer():
    """Windows 11's App Installer look: a flat blue tile with a white open
    box and an arrow going into it (the VeltOS Windows program runner)."""
    tile_d = rrect(28, 28, 200, 200, 40)
    return svg("App Installer (Windows program runner)",
               grad("tile", "#4F8CFF", "#2B45C8") + grad("box", "#FFFFFF", "#DCE6FF"),
               shadow(tile_d)
               + f'  <path d="{tile_d}" fill="url(#tile)"/>\n'
               # the open box
               + '  <path d="M 70 132 H 186 V 190 Q 186 200 176 200 H 80 Q 70 200 70 190 Z" fill="url(#box)"/>\n'
               + '  <path d="M 62 112 H 194 L 186 134 H 70 Z" fill="#FFFFFF" opacity="0.85"/>\n'
               + '  <path d="M 110 150 H 146" stroke="#2B45C8" stroke-width="8" stroke-linecap="round" opacity="0.35"/>\n'
               # the arrow coming down into it
               + '  <path d="M 128 46 V 96 M 106 76 L 128 98 L 150 76" fill="none" stroke="#FFFFFF" '
                 'stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>\n')


def clock():
    """Windows 11's Clock look: a dark blue clock with a white face and
    blue hands, light from the top left."""
    import math
    cx, cy, r = 128, 132, 100
    ticks = []
    for i in range(12):
        angle = math.radians(i * 30)
        inner = 84 if i % 3 == 0 else 90
        ticks.append(f'  <path d="M {cx + inner * math.sin(angle):.1f} {cy - inner * math.cos(angle):.1f} '
                     f'L {cx + 94 * math.sin(angle):.1f} {cy - 94 * math.cos(angle):.1f}" stroke="#3A4A6B" '
                     f'stroke-width="{6 if i % 3 == 0 else 4}" stroke-linecap="round"/>\n')
    return svg("Clock", grad("rim", "#2E62E8", "#15308F") + grad("face", "#FFFFFF", "#E6ECF7"),
               shadow(f"M {cx} {cy - r} A {r} {r} 0 1 1 {cx - 0.01} {cy - r} Z")
               + f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#rim)"/>\n'
               + f'  <circle cx="{cx}" cy="{cy}" r="{r - 14}" fill="url(#face)"/>\n'
               + "".join(ticks)
               # 10:08, as clocks are drawn
               + f'  <path d="M {cx} {cy} L {cx - 36} {cy - 34}" stroke="#15308F" stroke-width="10" stroke-linecap="round"/>\n'
               + f'  <path d="M {cx} {cy} L {cx + 52} {cy - 42}" stroke="#15308F" stroke-width="8" stroke-linecap="round"/>\n'
               + f'  <path d="M {cx} {cy + 18} L {cx + 20} {cy + 56}" stroke="#2FA8F0" stroke-width="4" stroke-linecap="round"/>\n'
               + f'  <circle cx="{cx}" cy="{cy}" r="8" fill="#15308F"/>\n'
               + f'  <circle cx="{cx}" cy="{cy}" r="3" fill="#FFFFFF"/>\n')


def calendar():
    """Windows 11's Calendar look: a blue calendar with two binding rings,
    a white sheet and a grid of days, one of them marked."""
    body_d = rrect(28, 46, 200, 178, 28)
    sheet_d = rrect(44, 96, 168, 112, 16)
    cells = []
    for row in range(3):
        for column in range(4):
            x, y = 62 + column * 36, 110 + row * 30
            marked = (row, column) == (1, 2)
            cells.append(f'  <rect x="{x}" y="{y}" width="24" height="20" rx="5" '
                         f'fill="{"url(#mark)" if marked else "#A9C8F5"}"/>\n')
    rings = "".join(f'  <rect x="{x}" y="28" width="18" height="42" rx="9" fill="url(#ring)"/>\n'
                    f'  <rect x="{x + 5}" y="34" width="8" height="24" rx="4" fill="#1A55C8" opacity="0.35"/>\n'
                    for x in (78, 160))
    return svg("Calendar", grad("body", "#3D8BF2", "#1747B8") + grad("sheet", "#FFFFFF", "#E6EDF8")
               + grad("ring", "#F4F7FC", "#C9D6EA") + grad("mark", "#2E6BE6", "#1747B8"),
               shadow(body_d)
               + f'  <path d="{body_d}" fill="url(#body)"/>\n'
               + f'  <path d="{sheet_d}" fill="url(#sheet)"/>\n'
               + "".join(cells) + rings)


def gear_path(cx, cy, outer, inner, teeth, tooth_frac=0.42):
    import math
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step - math.pi / 2
        half = step * tooth_frac / 2
        for ang, r in ((a - half * 1.25, inner), (a - half, outer), (a + half, outer), (a + half * 1.25, inner)):
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def settings():
    g = gear_path(128, 128, 104, 82, 8)
    return svg("Settings", grad("gear", "#8A94A3", "#5B6573") + grad("hub", "#3A7BEA", "#1C4FB5"),
               shadow(g)
               + f'  <path d="{g}" fill="url(#gear)" stroke-linejoin="round"/>\n'
               + '  <circle cx="128" cy="128" r="50" fill="#F4F6F9"/>\n'
               + '  <circle cx="128" cy="128" r="32" fill="url(#hub)"/>\n')


def task_manager():
    tile_d = rrect(24, 44, 208, 168, 22)
    return svg("Task Manager", grad("tile", "#2E7BE8", "#1A4FB0") + grad("area", "#9FE0FF", "#4FB4F5"),
               shadow(tile_d)
               + f'  <path d="{tile_d}" fill="url(#tile)"/>\n'
               + '  <path d="M 24 168 L 60 120 L 86 146 L 116 84 L 146 140 L 170 112 L 198 150 L 232 104 V 190 '
                 'Q 232 212 210 212 H 46 Q 24 212 24 190 Z" fill="url(#area)"/>\n'
               + '  <path d="M 24 168 L 60 120 L 86 146 L 116 84 L 146 140 L 170 112 L 198 150 L 232 104" '
                 'fill="none" stroke="#FFFFFF" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>\n')


def file_explorer():
    back = "M 20 66 Q 20 50 36 50 H 96 Q 106 50 113 58 L 122 68 H 220 Q 236 68 236 84 V 200 Q 236 216 220 216 H 36 Q 20 216 20 200 Z"
    front = "M 20 98 Q 20 86 32 86 H 224 Q 236 86 236 98 V 200 Q 236 216 220 216 H 36 Q 20 216 20 200 Z"
    return svg("File Explorer", grad("back", "#F2B12A", "#E0950E") + grad("front", "#FFE17D", "#FFC83D")
               + grad("tab", "#3FA0F6", "#1F6FD8"),
               shadow(back)
               + f'  <path d="{back}" fill="url(#back)"/>\n'
               + f'  <path d="{front}" fill="url(#front)"/>\n'
               + '  <path d="M 32 88 H 224" stroke="#FFFFFF" stroke-opacity="0.6" stroke-width="3" stroke-linecap="round"/>\n'
               + '  <path d="M 84 216 V 172 Q 84 160 96 160 H 160 Q 172 160 172 172 V 216 Z" fill="url(#tab)"/>\n'
               + '  <path d="M 104 186 H 152" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" opacity="0.85"/>\n')


def notepad():
    pad_d = rrect(48, 40, 160, 176, 16)
    rings = "".join(f'  <rect x="{x}" y="26" width="12" height="30" rx="6" fill="#26313D"/>\n' for x in (76, 106, 136, 166))
    return svg("Notepad", grad("pad", "#7FD7F7", "#3BAEEA") + grad("pages", "#9C6B47", "#6E4628"),
               shadow(pad_d)
               + '  <path d="M 52 204 H 204 V 222 Q 204 230 196 230 H 60 Q 52 230 52 222 Z" fill="url(#pages)"/>\n'
               + f'  <path d="{pad_d}" fill="url(#pad)"/>\n'
               + rings
               + '  <path d="M 80 96 H 176 M 80 128 H 176 M 80 160 H 150" stroke="#1E5E9E" stroke-width="10" stroke-linecap="round"/>\n')


def photos():
    tile_d = rrect(24, 40, 208, 176, 22)
    return svg("Photos", grad("sky", "#5FC2FF", "#1E7BE0") + grad("hill", "#FFFFFF", "#D7ECFF")
               + grad("hill2", "#B6E0FF", "#7CC3FA"),
               shadow(tile_d)
               + f'  <path d="{tile_d}" fill="url(#sky)"/>\n'
               + '  <circle cx="172" cy="90" r="18" fill="#FFE27A"/>\n'
               + '  <path d="M 24 186 L 92 116 L 140 166 L 166 140 L 232 196 V 194 Q 232 216 210 216 H 46 Q 24 216 24 194 Z" fill="url(#hill2)"/>\n'
               + '  <path d="M 24 196 L 92 128 L 164 200 L 178 216 H 46 Q 24 216 24 194 Z" fill="url(#hill)"/>\n')


def document_viewer():
    page_d = "M 60 24 H 156 L 204 72 V 220 Q 204 232 192 232 H 60 Q 48 232 48 220 V 36 Q 48 24 60 24 Z"
    return svg("Document Viewer", grad("page", "#FFFFFF", "#EDF1F6") + grad("band", "#F0533F", "#C8301F"),
               shadow(page_d)
               + f'  <path d="{page_d}" fill="url(#page)" stroke="#D3DAE4" stroke-width="2"/>\n'
               + '  <path d="M 156 24 V 60 Q 156 72 168 72 H 204 Z" fill="#D8DFE8"/>\n'
               + '  <path d="M 76 104 H 176 M 76 128 H 176 M 76 152 H 140" stroke="#AEB9C7" stroke-width="9" stroke-linecap="round"/>\n'
               + '  <rect x="36" y="168" width="120" height="48" rx="10" fill="url(#band)"/>\n'
               + '  <path d="M 58 204 V 180 H 66 Q 76 180 76 189 Q 76 198 66 198 H 58 M 86 204 V 180 H 94 Q 106 180 106 192 '
                 'Q 106 204 94 204 Z M 116 204 V 180 H 132 M 116 192 H 128" fill="none" stroke="#FFFFFF" '
                 'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>\n')


def archive():
    """A yellow folder with a zipper, like Windows' compressed folders."""
    back = "M 20 66 Q 20 50 36 50 H 96 Q 106 50 113 58 L 122 68 H 220 Q 236 68 236 84 V 200 Q 236 216 220 216 H 36 Q 20 216 20 200 Z"
    front = "M 20 98 Q 20 86 32 86 H 224 Q 236 86 236 98 V 200 Q 236 216 220 216 H 36 Q 20 216 20 200 Z"
    teeth = "".join(
        f'  <rect x="{120 if i % 2 == 0 else 130}" y="{90 + i * 12}" width="10" height="8" rx="2" fill="#5B6573"/>\n'
        for i in range(7))
    return svg("Archive", grad("back", "#F2B12A", "#E0950E") + grad("front", "#FFE17D", "#FFC83D")
               + grad("pull", "#8A94A3", "#4A5361"),
               shadow(back)
               + f'  <path d="{back}" fill="url(#back)"/>\n'
               + f'  <path d="{front}" fill="url(#front)"/>\n'
               + '  <path d="M 32 88 H 224" stroke="#FFFFFF" stroke-opacity="0.6" stroke-width="3" stroke-linecap="round"/>\n'
               + teeth
               + '  <rect x="112" y="174" width="32" height="34" rx="7" fill="url(#pull)"/>\n'
               + '  <rect x="122" y="184" width="12" height="14" rx="3" fill="#F2F4F7"/>\n')


def media_player():
    tile_d = rrect(28, 28, 200, 200, 44)
    return svg("Media Player", grad("tile", "#FF9A4D", "#F0436F", "1", "1"),
               shadow(tile_d)
               + f'  <path d="{tile_d}" fill="url(#tile)"/>\n'
               + '  <path d="M 104 84 Q 104 70 116 77 L 176 117 Q 188 128 176 139 L 116 179 Q 104 186 104 172 Z" fill="#FFFFFF"/>\n')


def disk_management():
    """The local disk (as in File Explorer) with a partition chart, like
    Windows' Disk Management."""
    top = "M 26 120 L 58 70 H 182 L 206 108"
    return svg("Disk Management", grad("top", "#F4F6F8", "#DDE2E8") + grad("side", "#B9C1CB", "#8E98A5")
               + grad("pie", "#5FC2FF", "#2F7BE6") + grad("slice", "#7BE0B0", "#2FB673"),
               shadow("M 26 120 H 206 V 196 Q 206 208 194 208 H 38 Q 26 208 26 196 Z")
               + f'  <path d="{top} L 206 120 Z" fill="url(#top)" stroke="#A9B2BD" stroke-width="3" stroke-linejoin="round"/>\n'
               + '  <rect x="26" y="120" width="180" height="84" rx="12" fill="url(#side)"/>\n'
               + '  <rect x="26" y="120" width="180" height="5" fill="#FFFFFF" opacity="0.5"/>\n'
               + '  <rect x="46" y="156" width="88" height="10" rx="5" fill="#5E6873"/>\n'
               + '  <circle cx="176" cy="161" r="9" fill="#36C26A"/>\n'
               + '  <circle cx="186" cy="84" r="50" fill="#FFFFFF"/>\n'
               + '  <circle cx="186" cy="84" r="42" fill="url(#pie)"/>\n'
               + '  <path d="M 186 84 V 42 A 42 42 0 0 1 226 98 Z" fill="url(#slice)" stroke="#FFFFFF" stroke-width="4" '
                 'stroke-linejoin="round"/>\n')


def program():
    """A program without an icon of its own (application-x-executable):
    Windows' plain window with a blue title bar. Fluent's drew a window
    with an exclamation mark, which looked like a warning in Task Manager's
    background processes and in "Open with"."""
    body = rrect(28, 48, 200, 164, 18)
    return svg("Program", grad("body", "#FFFFFF", "#E9EDF3") + grad("bar", "#4F8DF0", "#2F6BE6"),
               shadow(body)
               + f'  <path d="{body}" fill="url(#body)" stroke="#C9D1DC" stroke-width="3"/>\n'
               + '  <path d="M 46 48 H 210 Q 228 48 228 66 V 88 H 28 V 66 Q 28 48 46 48 Z" fill="url(#bar)"/>\n'
               + '  <circle cx="198" cy="68" r="5" fill="#FFFFFF" opacity="0.9"/>\n'
               + '  <circle cx="180" cy="68" r="5" fill="#FFFFFF" opacity="0.7"/>\n'
               + '  <rect x="52" y="112" width="104" height="10" rx="5" fill="#C9D1DC"/>\n'
               + '  <rect x="52" y="136" width="152" height="10" rx="5" fill="#DCE2EA"/>\n'
               + '  <rect x="52" y="160" width="128" height="10" rx="5" fill="#DCE2EA"/>\n')


def graphics_cards():
    """A graphics card seen from the side: the metal bracket with display
    ports, the shroud with two fans and the gold PCI Express edge."""
    shroud = rrect(40, 58, 196, 128, 20)

    def fan(cx, cy):
        blade = f"M {cx} {cy} Q {cx + 4} {cy - 28} {cx + 24} {cy - 22} Q {cx + 14} {cy - 8} {cx} {cy} Z"
        blades = "".join(f'  <path d="{blade}" fill="url(#blade)" transform="rotate({a} {cx} {cy})"/>\n'
                         for a in range(0, 360, 60))
        return (f'  <circle cx="{cx}" cy="{cy}" r="38" fill="url(#rim)"/>\n'
                f'  <circle cx="{cx}" cy="{cy}" r="32" fill="#1D2129"/>\n'
                + blades
                + f'  <circle cx="{cx}" cy="{cy}" r="9" fill="url(#hub)"/>\n')

    return svg("Graphics Cards", grad("shroud", "#5B6273", "#2C313B") + grad("bracket", "#E9EDF2", "#AEB6C1")
               + grad("rim", "#C9CFD8", "#7D8693") + grad("blade", "#7CC4FF", "#2F6BE6", "1", "1")
               + grad("hub", "#FFFFFF", "#C6CDD7") + grad("gold", "#F8D271", "#D9961E"),
               shadow(shroud)
               + '  <path d="M 84 186 H 196 V 204 Q 196 210 190 210 H 90 Q 84 210 84 204 Z" fill="url(#gold)"/>\n'
               + '  <path d="M 98 192 V 208 M 110 192 V 208 M 122 192 V 208 M 146 192 V 208 M 158 192 V 208 '
                 'M 170 192 V 208 M 182 192 V 208" stroke="#B57A12" stroke-width="4" stroke-linecap="round"/>\n'
               + f'  <path d="{shroud}" fill="url(#shroud)"/>\n'
               + '  <path d="M 58 72 H 218" stroke="#2FA8F0" stroke-width="5" stroke-linecap="round"/>\n'
               + fan(96, 124) + fan(180, 124)
               + '  <path d="M 20 44 H 44 V 204 Q 44 214 34 214 H 20 Z" fill="url(#bracket)"/>\n'
               + '  <rect x="26" y="70" width="12" height="30" rx="3" fill="#3B414D"/>\n'
               + '  <rect x="26" y="110" width="12" height="22" rx="3" fill="#3B414D"/>\n'
               + '  <rect x="26" y="142" width="12" height="22" rx="3" fill="#3B414D"/>\n')


# Office (LibreOffice, veltos-office): the composition of Microsoft 365's
# Windows 11 icons (a coloured tile with the app's initial in front of a
# page, sheet or slide), drawn here: W, X and P in Word blue, Excel green
# and PowerPoint orange, the apps' names in Start being Word, Excel and
# PowerPoint (product owner, 2026-10-22). Microsoft's own icon files are
# not used. The same three drawings stand for the file types (MIME icons
# below).
OFFICE_PAGE_D = "M 108 20 H 196 L 236 60 V 224 Q 236 236 224 236 H 108 Q 96 236 96 224 V 32 Q 96 20 108 20 Z"
OFFICE_TILE_D = rrect(16, 72, 124, 124, 22)
OFFICE_LETTERS = {
    # Thick strokes with round caps, centred in the tile (16..140 x 72..196).
    "W": "M 44 110 L 60 160 L 78 122 L 96 160 L 112 110",
    "X": "M 52 108 L 104 172 M 104 108 L 52 172",
    "P": "M 58 166 V 106 H 86 Q 108 106 108 128 Q 108 150 86 150 H 58",
}


def office_icon(what, letter, dark, mid, light, ink, content):
    """Tile (three shades of the app colour, light from the top left), the
    letter, and the page behind with the app's content lines."""
    return svg(what, grad("page", "#FFFFFF", "#EEF1F6") + grad("tile", light, dark, x2="1", y2="1")
               + grad("edge", mid, dark),
               shadow(OFFICE_PAGE_D)
               + f'  <path d="{OFFICE_PAGE_D}" fill="url(#page)" stroke="#D3DAE4" stroke-width="2"/>\n'
               + '  <path d="M 196 20 V 50 Q 196 60 206 60 H 236 Z" fill="#D8DFE8"/>\n'
               + content
               + shadow(OFFICE_TILE_D)
               + f'  <path d="{OFFICE_TILE_D}" fill="url(#tile)"/>\n'
               + f'  <path d="M 16 134 V 174 Q 16 196 38 196 H 118 Q 140 196 140 174 V 134 Z" fill="url(#edge)" opacity="0.55"/>\n'
               + f'  <path d="{OFFICE_LETTERS[letter]}" fill="none" stroke="#FFFFFF" stroke-width="15" '
                 'stroke-linecap="round" stroke-linejoin="round"/>\n')


def word_processor():
    lines = ('  <path d="M 152 92 H 212" stroke="#185ABD" stroke-width="10" stroke-linecap="round"/>\n'
             '  <path d="M 152 120 H 216 M 152 144 H 216 M 152 168 H 216 M 152 192 H 192" stroke="#8FB4EC" '
             'stroke-width="7" stroke-linecap="round"/>\n')
    return office_icon("Word Processor", "W", "#103F8F", "#185ABD", "#3E86E8", "#185ABD", lines)


def spreadsheet():
    grid = ('  <path d="M 150 84 H 222 V 204 H 150 Z" fill="#E4F4EA" stroke="#107C41" stroke-width="3"/>\n'
            '  <path d="M 150 84 H 222 V 108 H 150 Z" fill="#107C41"/>\n'
            '  <path d="M 150 132 H 222 M 150 156 H 222 M 150 180 H 222 M 174 108 V 204 M 198 108 V 204" '
            'stroke="#7CC79A" stroke-width="3"/>\n')
    return office_icon("Spreadsheet", "X", "#0B5A2F", "#107C41", "#2DA860", "#107C41", grid)


def presentation():
    chart = ('  <rect x="150" y="80" width="76" height="52" rx="6" fill="#FFE1D4"/>\n'
             '  <circle cx="176" cy="106" r="16" fill="#F7B99C"/>\n'
             '  <path d="M 176 106 V 90 A 16 16 0 0 1 191 112 Z" fill="#C43E1C"/>\n'
             '  <rect x="200" y="96" width="8" height="26" rx="2" fill="#E8744F"/>\n'
             '  <rect x="212" y="88" width="8" height="34" rx="2" fill="#C43E1C"/>\n'
             '  <path d="M 152 152 H 216 M 152 176 H 216 M 152 200 H 192" stroke="#F4B59E" '
             'stroke-width="7" stroke-linecap="round"/>\n')
    return office_icon("Presentation", "P", "#8F2A10", "#C43E1C", "#EB6A45", "#C43E1C", chart)

# drawing -> icon names it is installed under
NAMES = {
    calculator: ["veltos-calculator", "accessories-calculator", "org.kde.kcalc", "calc"],
    camera: ["veltos-camera", "camera-app", "org.kde.kamoso", "cheese", "org.gnome.Cheese"],
    mail: ["veltos-mail", "thunderbird", "internet-mail", "mail-client", "org.kde.kmail2"],
    calendar: ["veltos-calendar", "office-calendar", "x-office-calendar", "org.kde.korganizer", "korganizer",
               "org.gnome.Calendar", "gnome-calendar"],
    snipping_tool: ["veltos-snip", "org.kde.spectacle", "spectacle", "accessories-screenshot"],
    store: ["veltos-store", "org.kde.discover", "plasmadiscover"],
    settings: ["veltos-settings", "systemsettings", "preferences-system"],
    task_manager: ["veltos-taskmanager", "org.kde.plasma-systemmonitor", "utilities-system-monitor"],
    file_explorer: ["veltos-explorer", "system-file-manager", "file-manager", "org.kde.dolphin"],
    notepad: ["veltos-notepad", "org.kde.kwrite", "kwrite", "accessories-text-editor", "org.kde.kate", "kate"],
    photos: ["veltos-photos", "org.kde.gwenview", "gwenview", "image-viewer"],
    document_viewer: ["veltos-pdf", "org.kde.okular", "okular"],
    archive: ["veltos-archive", "org.kde.ark", "ark", "file-roller", "utilities-file-archiver"],
    media_player: ["veltos-media", "org.kde.haruna", "multimedia-video-player", "vlc"],
    disk_management: ["veltos-disks", "partitionmanager", "org.kde.partitionmanager", "gnome-disks",
                      "org.gnome.DiskUtility"],
    graphics_cards: ["veltos-graphics"],
    app_installer: ["veltos-run", "veltos-winapps"],
    clock: ["veltos-clock", "org.kde.kclock", "kclock", "preferences-system-time", "clock"],
    word_processor: ["libreoffice-writer", "libreoffice3-writer", "libreoffice34-writer"],
    spreadsheet: ["libreoffice-calc", "libreoffice3-calc", "libreoffice34-calc"],
    presentation: ["libreoffice-impress", "libreoffice3-impress", "libreoffice34-impress"],
}

# Office and PDF file types (mimetypes/) show the same drawings, as
# Windows shows documents with their app's picture.
DOCUMENT_MIMETYPES = {
    word_processor: ["x-office-document", "application-msword", "application-rtf", "text-rtf",
                     "application-vnd.openxmlformats-officedocument.wordprocessingml.document",
                     "application-vnd.openxmlformats-officedocument.wordprocessingml.template",
                     "application-vnd.ms-word.document.macroenabled.12",
                     "application-vnd.oasis.opendocument.text", "application-vnd.oasis.opendocument.text-template"],
    spreadsheet: ["x-office-spreadsheet", "application-vnd.ms-excel", "text-csv",
                  "application-vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                  "application-vnd.openxmlformats-officedocument.spreadsheetml.template",
                  "application-vnd.ms-excel.sheet.macroenabled.12",
                  "application-vnd.oasis.opendocument.spreadsheet",
                  "application-vnd.oasis.opendocument.spreadsheet-template"],
    presentation: ["x-office-presentation", "application-vnd.ms-powerpoint",
                   "application-vnd.openxmlformats-officedocument.presentationml.presentation",
                   "application-vnd.openxmlformats-officedocument.presentationml.slideshow",
                   "application-vnd.openxmlformats-officedocument.presentationml.template",
                   "application-vnd.ms-powerpoint.presentation.macroenabled.12",
                   "application-vnd.oasis.opendocument.presentation",
                   "application-vnd.oasis.opendocument.presentation-template"],
    document_viewer: ["application-pdf", "application-x-pdf"],
    program: ["application-x-executable"],
}


# Archive file types (mimetypes/) show the zipped folder, like Windows'
# .zip files; also .rar, .7z and the tar archives VeltOS Archive opens.
ARCHIVE_MIMETYPES = ["application-zip", "application-x-zip", "application-x-zip-compressed",
                     "application-x-rar", "application-vnd.rar", "application-x-rar-compressed",
                     "application-x-7z-compressed", "application-x-7zip", "application-x-tar",
                     "application-x-compressed-tar", "application-x-bzip-compressed-tar",
                     "application-x-xz-compressed-tar", "application-x-zstd-compressed-tar",
                     "application-x-7z-compressed-tar", "application-gzip", "application-x-gzip",
                     "application-x-xz", "application-x-bzip", "application-x-bzip2", "application-zstd",
                     "application-x-archive", "package-x-generic"]
MIME_OUT = OUT.parent / "mimetypes"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MIME_OUT.mkdir(parents=True, exist_ok=True)
    for folder in (OUT, MIME_OUT):
        for old in folder.glob("*.svg"):
            old.unlink()
    for draw, names in NAMES.items():
        text = draw()
        for name in names:
            (OUT / f"{name}.svg").write_text(text, encoding="utf-8", newline="\n")
    zipped = archive()
    for name in ARCHIVE_MIMETYPES:
        (MIME_OUT / f"{name}.svg").write_text(zipped, encoding="utf-8", newline="\n")
    for draw, names in DOCUMENT_MIMETYPES.items():
        text = draw()
        for name in names:
            (MIME_OUT / f"{name}.svg").write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
