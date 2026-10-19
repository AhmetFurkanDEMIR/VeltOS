"""VeltOS GTK themes: Breeze with Windows 11 caption buttons.

GTK programs that draw their own title bar (Firefox, GTK 3 programs with a
header bar) take the minimise/maximise/close buttons from the GTK theme.
Breeze, KDE's GTK theme, draws small round KDE buttons; KDE's GTK settings
module can copy the window frame's buttons into GTK, but produced empty
images for the VeltOS (Aurorae) frames (VM test, 2026-10-19). The VeltOS
themes import Breeze, whose colours follow the KDE colour scheme through
~/.config/gtk-3.0/colors.css, and replace only the caption buttons with
images drawn by the same code as the window frames (tools/fluent.py), so
GTK and KDE windows have identical buttons.

    themes/VeltOS/gtk-3.0/{gtk.css,gtk-dark.css}, gtk-4.0/{gtk.css,gtk-dark.css}
    themes/VeltOS/{gtk-3.0,gtk-4.0}/assets/<button>-<state>.svg
"""

from pathlib import Path

import fluent

THEME = "VeltOS"
# GTK button names -> glyph drawn by fluent.caption_glyph.
BUTTONS = {"close": "close", "minimize": "minimize", "maximize": "maximize", "maximized": "restore"}
STATES = ("normal", "hover", "active", "backdrop-normal", "backdrop-hover", "backdrop-active")
GTK_VERSIONS = ("gtk-3.0", "gtk-4.0")


def button_svg(button, state, variant):
    """One 46 x 32 caption button image."""
    kind = BUTTONS[button]
    c = fluent.CAPTION_COLOURS[variant]
    red = kind == "close"
    backdrop = state.startswith("backdrop-")
    base = state.removeprefix("backdrop-")
    background = None
    colour, opacity = (c["inactive"] if backdrop else c["glyph"]), 1.0
    if base == "hover":
        background = (fluent.CLOSE_RED, 1.0) if red else c["hover"]
        colour = "#ffffff" if red else c["glyph"]
    elif base == "active":
        background = (fluent.CLOSE_RED, 0.85) if red else c["pressed"]
        colour, opacity = ("#ffffff", 0.7) if red else (c["glyph"], 0.8)
    w, h = fluent.CAPTION_W, fluent.CAPTION_H
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    if background:
        # GTK draws the button inside the window; no rounded window corner here.
        parts.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{background[0]}" '
                     f'opacity="{background[1]:g}"/>')
    parts.append(fluent.caption_glyph(kind, 0, colour, opacity))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def titlebuttons_css():
    selectors = "headerbar button.titlebutton, .titlebar button.titlebutton"
    w, h = fluent.CAPTION_W, fluent.CAPTION_H
    lines = [
        "/* VeltOS: Windows 11 caption buttons (46 x 32, thin glyphs, red close). */",
        f"{selectors} {{",
        f"  min-width: {w}px; min-height: {h}px; margin: 0; padding: 0;",
        "  border: none; border-radius: 0; box-shadow: none; outline: none;",
        "  background-color: transparent; background-repeat: no-repeat;",
        f"  background-position: center; background-size: {w}px {h}px;",
        "}",
        "headerbar button.titlebutton image, .titlebar button.titlebutton image { opacity: 0; }",
        "headerbar, .titlebar { padding-right: 0; }",
    ]
    pseudo = {"normal": "", "hover": ":hover", "active": ":active",
              "backdrop-normal": ":backdrop", "backdrop-hover": ":backdrop:hover",
              "backdrop-active": ":backdrop:active"}
    for button in BUTTONS:
        cls = "maximize" if button == "maximized" else button
        prefix = ".maximized " if button == "maximized" else ""
        for state in STATES:
            sel = ", ".join(f"{prefix}{base}.{cls}{pseudo[state]}" for base in
                            ("headerbar button.titlebutton", ".titlebar button.titlebutton"))
            lines.append(f'{sel} {{ background-image: url("assets/{button}-{state}.svg"); }}')
    return "\n".join(lines) + "\n"


def build(root):
    """Write the VeltOS GTK theme into root/usr/share/themes."""
    base = root / "usr/share/themes" / THEME
    css = titlebuttons_css()
    for gtk in GTK_VERSIONS:
        d = base / gtk
        for variant, sheet, breeze in (("light", "gtk.css", "gtk.css"), ("dark", "gtk-dark.css", "gtk-dark.css")):
            assets = d / ("assets" if variant == "light" else "assets-dark")
            assets.mkdir(parents=True, exist_ok=True)
            for button in BUTTONS:
                for state in STATES:
                    (assets / f"{button}-{state}.svg").write_text(button_svg(button, state, variant),
                                                                  encoding="utf-8", newline="\n")
            text = (f"/* VeltOS GTK theme ({variant}): Breeze with Windows 11 caption buttons.\n"
                    f"   {fluent.ATTRIBUTION} (button glyphs). */\n"
                    f'@import url("../../Breeze/{gtk}/{breeze}");\n\n'
                    + css.replace('url("assets/', f'url("{assets.name}/'))
            (d / sheet).write_text(text, encoding="utf-8", newline="\n")
    (base / "index.theme").write_text(
        "[Desktop Entry]\nType=X-GNOME-Metatheme\nName=VeltOS\n"
        "Comment=Breeze with Windows 11 caption buttons (VeltOS)\nEncoding=UTF-8\n\n"
        "[X-GNOME-Metatheme]\nGtkTheme=VeltOS\nIconTheme=Fluent\nCursorTheme=Fluent-cursors\n",
        encoding="utf-8", newline="\n")
    return base


if __name__ == "__main__":
    import sys
    print(build(Path(sys.argv[1])))
