#!/usr/bin/python3
"""Dev aid (VM only, as root): try acrylic values on the installed VeltOS
Plasma themes (translucent popup and taskbar backgrounds, contrast effect).
Usage: acrylic-proto.py LIGHT_POP LIGHT_POP_OP LIGHT_BAR LIGHT_BAR_OP
                        DARK_POP DARK_POP_OP DARK_BAR DARK_BAR_OP
                        LIGHT_CONTRAST LIGHT_INTENSITY DARK_CONTRAST DARK_INTENSITY SATURATION
Keeps a pristine copy in /var/tmp/acrylic-orig on the first run."""
import gzip
import re
import shutil
import sys
from pathlib import Path

ROOT = Path("/usr/share/plasma/desktoptheme")
ORIG = Path("/var/tmp/acrylic-orig")
a = sys.argv[1:]
values = {
    "VeltOS": {"pop": (a[0], a[1]), "bar": (a[2], a[3]), "contrast": (a[8], a[9])},
    "VeltOS-Dark": {"pop": (a[4], a[5]), "bar": (a[6], a[7]), "contrast": (a[10], a[11])},
}
saturation = a[12]

if not ORIG.exists():
    for theme in values:
        shutil.copytree(ROOT / theme, ORIG / theme)


def paint(svg, groups, colour, opacity):
    def group(match):
        def element(m):
            tag = m.group(0)
            style = re.search(r'style="([^"]*)"', tag)
            if not style:
                return tag
            text = style.group(1)
            if "fill:none" in text or "fill:#000000" in text:
                return tag
            if "currentColor" not in text and "#ffffff" not in text and "#f9fafc" not in text and \
                    "ColorScheme-Background" not in tag:
                return tag
            tag = tag.replace(' class="ColorScheme-Background"', "")
            text = re.sub(r"fill:[^;]*", f"fill:{colour}", text) if "fill:" in text else f"fill:{colour};" + text
            text = re.sub(r"(?<![-\w])opacity:[0-9.]+", f"opacity:{opacity}", text) if re.search(
                r"(?<![-\w])opacity:", text) else text + f";opacity:{opacity}"
            tag = tag.replace(style.group(0), f'style="{text}"')
            tag = re.sub(r'\sfill="currentColor"', "", tag)
            return tag
        return re.sub(r"<(?:rect|path)\b[^>]*>", element, match.group(0))
    return re.sub(r'<g\b[^>]*id="(?:%s)"[^>]*>.*?</g>' % "|".join(groups), group, svg, flags=re.S)


PIECES = ["center", "top", "bottom", "left", "right", "topleft", "topright", "bottomleft", "bottomright"]
for theme, v in values.items():
    for rel, key in (("translucent/dialogs/background.svgz", "pop"),
                     ("translucent/widgets/panel-background.svgz", "bar")):
        src = ORIG / theme / rel
        svg = gzip.decompress(src.read_bytes()).decode("utf-8")
        svg = paint(svg, PIECES, *v[key])
        (ROOT / theme / rel).write_bytes(gzip.compress(svg.encode("utf-8")))
    rc = (ORIG / theme / "plasmarc").read_text(encoding="utf-8")
    contrast, intensity = v["contrast"]
    rc = re.sub(r"\[ContrastEffect\].*?(?=\n\[|\Z)",
                f"[ContrastEffect]\nenabled=true\ncontrast={contrast}\nintensity={intensity}\nsaturation={saturation}\n",
                rc, flags=re.S)
    (ROOT / theme / "plasmarc").write_text(rc, encoding="utf-8")
print("ok")
