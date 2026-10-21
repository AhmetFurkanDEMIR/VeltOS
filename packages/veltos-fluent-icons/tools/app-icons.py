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
    body_d = ("M 40 76 Q 40 60 56 60 H 86 L 100 40 Q 104 34 112 34 H 144 Q 152 34 156 40 L 170 60 "
              "H 200 Q 216 60 216 76 V 196 Q 216 212 200 212 H 56 Q 40 212 40 196 Z")
    return svg("Camera", grad("body", "#7B8594", "#525C6A") + grad("lens", "#C38BFF", "#3FA8F6", "1", "1")
               + grad("ring", "#FFFFFF", "#E2E7EE"),
               shadow(body_d)
               + '  <rect x="54" y="46" width="34" height="18" rx="6" fill="#2FA8F0"/>\n'
               + f'  <path d="{body_d}" fill="url(#body)"/>\n'
               + '  <path d="M 56 63 H 200" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="3" stroke-linecap="round"/>\n'
               + '  <circle cx="128" cy="136" r="56" fill="url(#ring)"/>\n'
               + '  <circle cx="128" cy="136" r="42" fill="url(#lens)"/>\n'
               + '  <ellipse cx="114" cy="120" rx="13" ry="9" fill="#FFFFFF" opacity="0.35"/>\n'
               + '  <circle cx="192" cy="88" r="7" fill="#DDE3EA"/>\n')


def mail():
    env_d = "M 24 104 L 128 36 L 232 104 V 196 Q 232 214 214 214 H 42 Q 24 214 24 196 Z"
    return svg("Mail", grad("back", "#1A64C8", "#0F4AA0") + grad("front", "#45B9F9", "#1F86E8", "0.2", "1")
               + grad("paper", "#FFFFFF", "#E8EEF5"),
               shadow(env_d)
               + f'  <path d="{env_d}" fill="url(#back)"/>\n'
               + '  <rect x="58" y="70" width="140" height="104" rx="8" fill="url(#paper)"/>\n'
               + '  <path d="M 80 98 H 176 M 80 118 H 150" stroke="#9FB4CC" stroke-width="7" stroke-linecap="round"/>\n'
               + '  <path d="M 24 112 L 128 176 L 232 112 V 196 Q 232 214 214 214 H 42 Q 24 214 24 196 Z" fill="url(#front)"/>\n'
               + '  <path d="M 24 214 L 108 152 Q 128 140 148 152 L 232 214 Z" fill="#5CC7FF" opacity="0.55"/>\n')


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


# Office (LibreOffice, veltos-office): a page, a sheet and a slide in the
# family's colours. No letters on them: Microsoft's Office icons are marked
# with letters, VeltOS' are not copies.
PAGE_D = "M 60 24 H 156 L 204 72 V 220 Q 204 232 192 232 H 60 Q 48 232 48 220 V 36 Q 48 24 60 24 Z"


def word_processor():
    pencil = ('  <g transform="rotate(-45 186 186)">\n'
              '    <rect x="150" y="172" width="78" height="28" rx="6" fill="url(#pencil)"/>\n'
              '    <rect x="214" y="172" width="14" height="28" rx="4" fill="#F4A9B8"/>\n'
              '    <path d="M 150 172 L 126 186 L 150 200 Z" fill="#F6D7A7"/>\n'
              '    <path d="M 134 181 L 126 186 L 134 191 Z" fill="#26313D"/>\n'
              '  </g>\n')
    return svg("Word Processor", grad("page", "#FFFFFF", "#EDF1F6") + grad("ink", "#4F8BFF", "#1F4FD6")
               + grad("pencil", "#3D7BFF", "#1E4FD0"),
               shadow(PAGE_D)
               + f'  <path d="{PAGE_D}" fill="url(#page)" stroke="#D3DAE4" stroke-width="2"/>\n'
               + '  <path d="M 156 24 V 60 Q 156 72 168 72 H 204 Z" fill="#D8DFE8"/>\n'
               + '  <path d="M 76 72 H 132" stroke="url(#ink)" stroke-width="12" stroke-linecap="round"/>\n'
               + '  <path d="M 76 104 H 176 M 76 128 H 176 M 76 152 H 176 M 76 176 H 128" stroke="#5B8DEF" '
                 'stroke-width="8" stroke-linecap="round"/>\n'
               + pencil)


def spreadsheet():
    sheet_d = rrect(28, 36, 200, 184, 18)
    cells = "".join(f'  <path d="M {x} 80 V 220" stroke="#C5CED9" stroke-width="3"/>\n' for x in (92, 160))
    cells += "".join(f'  <path d="M 28 {y} H 228" stroke="#C5CED9" stroke-width="3"/>\n' for y in (116, 152, 188))
    return svg("Spreadsheet", grad("sheet", "#FFFFFF", "#EDF1F6") + grad("green", "#3CC47C", "#13894A"),
               shadow(sheet_d)
               + f'  <path d="{sheet_d}" fill="url(#sheet)" stroke="#D3DAE4" stroke-width="2"/>\n'
               + '  <path d="M 46 36 H 210 Q 228 36 228 54 V 80 H 28 V 54 Q 28 36 46 36 Z" fill="url(#green)"/>\n'
               + '  <path d="M 46 39 H 210" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="3" stroke-linecap="round"/>\n'
               + cells
               + '  <rect x="92" y="116" width="68" height="36" fill="#D6F5E3" stroke="#1FA35C" stroke-width="5"/>\n'
               + '  <rect x="155" y="147" width="10" height="10" fill="#1FA35C"/>\n')


def presentation():
    frame_d = rrect(24, 32, 208, 148, 18)
    return svg("Presentation", grad("frame", "#FF8A3D", "#E8501E") + grad("slide", "#FFFFFF", "#F1F3F6")
               + grad("legs", "#7B8594", "#525C6A"),
               '  <path d="M 128 176 V 206 M 128 196 L 96 232 M 128 196 L 160 232" stroke="url(#legs)" '
               'stroke-width="9" stroke-linecap="round" fill="none"/>\n'
               + shadow(frame_d)
               + f'  <path d="{frame_d}" fill="url(#frame)"/>\n'
               + '  <path d="M 42 35 H 214" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="3" stroke-linecap="round"/>\n'
               + '  <rect x="38" y="46" width="180" height="120" rx="8" fill="url(#slide)"/>\n'
               + '  <circle cx="96" cy="106" r="36" fill="#FFD3B8"/>\n'
               + '  <path d="M 96 106 V 70 A 36 36 0 0 1 130 118 Z" fill="url(#frame)"/>\n'
               + '  <rect x="146" y="112" width="14" height="30" rx="3" fill="#FBB48A"/>\n'
               + '  <rect x="166" y="94" width="14" height="48" rx="3" fill="#F57A3F"/>\n'
               + '  <rect x="186" y="78" width="14" height="64" rx="3" fill="#E8501E"/>\n')


# drawing -> icon names it is installed under
NAMES = {
    calculator: ["veltos-calculator", "accessories-calculator", "org.kde.kcalc", "calc"],
    camera: ["veltos-camera", "camera-app", "org.kde.kamoso", "cheese", "org.gnome.Cheese"],
    mail: ["veltos-mail", "thunderbird", "internet-mail", "mail-client", "org.kde.kmail2"],
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
