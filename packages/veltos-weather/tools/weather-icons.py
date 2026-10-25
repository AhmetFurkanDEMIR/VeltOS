#!/usr/bin/env python3
"""Draws VeltOS Weather's condition pictures (veltos_weather/qml/icons/*.svg)
and the small line glyphs of its details.

Original VeltOS drawings in the look of Windows 11's Weather app: a warm
sun, a pale yellow moon, soft white clouds that darken with rain, blue
drops, white flakes and a yellow bolt, on a 64 x 64 grid with gradients
lit from the top. Run it after changing a drawing:

    python3 tools/weather-icons.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "veltos_weather" / "qml" / "icons"
HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">\n'
        '  <!-- {what}: VeltOS artwork (tools/weather-icons.py). SPDX-License-Identifier: CC-BY-SA-4.0 -->\n')


def grad(gid, top, bottom, y1=0, y2=64):
    return (f'    <linearGradient id="{gid}" x1="0" y1="{y1}" x2="0" y2="{y2}" gradientUnits="userSpaceOnUse">\n'
            f'      <stop offset="0" stop-color="{top}"/>\n      <stop offset="1" stop-color="{bottom}"/>\n'
            '    </linearGradient>\n')


DEFS = (grad("sun", "#FFE16B", "#FFA41B", 6, 46) + grad("ray", "#FFD448", "#FFB01F", 0, 52)
        + grad("moon", "#FFF1BF", "#F4C95A", 6, 46)
        + grad("cloud", "#FFFFFF", "#CBD5E3", 16, 50) + grad("dark", "#C3CCDA", "#8793A8", 16, 50)
        + grad("storm", "#9AA5B8", "#5D6880", 14, 48) + grad("drop", "#5BB8FF", "#1F7AE0", 40, 62)
        + grad("bolt", "#FFE36B", "#FFAA12", 34, 62))


def svg(what, body):
    return HEAD.format(what=what) + "  <defs>\n" + DEFS + "  </defs>\n" + body + "</svg>\n"


def sun(cx=32, cy=32, r=12, rays=True):
    import math
    parts = []
    if rays:
        for i in range(8):
            a = math.radians(i * 45)
            x1, y1 = cx + (r + 5) * math.cos(a), cy + (r + 5) * math.sin(a)
            x2, y2 = cx + (r + 10) * math.cos(a), cy + (r + 10) * math.sin(a)
            parts.append(f'  <path d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}" stroke="url(#ray)" '
                         f'stroke-width="{max(2.5, r / 4):.1f}" stroke-linecap="round"/>\n')
    parts.append(f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sun)"/>\n')
    return "".join(parts)


def moon(cx=32, cy=30, r=15):
    """A crescent: a disc with a second, offset disc cut away."""
    return (f'  <mask id="cut"><rect width="64" height="64" fill="#fff"/>'
            f'<circle cx="{cx + r * 0.62:.1f}" cy="{cy - r * 0.42:.1f}" r="{r * 0.86:.1f}" fill="#000"/></mask>\n'
            f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#moon)" mask="url(#cut)"/>\n')


def cloud(fill="cloud", dx=0, dy=0, s=1.0):
    """A cloud with a flat, rounded base: one rounded rectangle and three
    domes in one gradient."""
    def t(x, y):
        return 32 + (x - 32) * s + dx, 36 + (y - 36) * s + dy
    x0, y0 = t(10, 32)
    x1, y1 = t(25, 30)
    x2, y2 = t(37, 26)
    x3, y3 = t(48, 33)
    return (f'  <g fill="url(#{fill})">\n'
            f'    <rect x="{x0:.1f}" y="{y0:.1f}" width="{44 * s:.1f}" height="{17 * s:.1f}" rx="{8.5 * s:.1f}"/>\n'
            f'    <circle cx="{x1:.1f}" cy="{y1:.1f}" r="{10 * s:.1f}"/>\n'
            f'    <circle cx="{x2:.1f}" cy="{y2:.1f}" r="{13 * s:.1f}"/>\n'
            f'    <circle cx="{x3:.1f}" cy="{y3:.1f}" r="{8 * s:.1f}"/>\n'
            '  </g>\n')


def drops(xs, top=48, length=8, heavy=False):
    width = 3.6 if heavy else 3
    return "".join(f'  <path d="M {x} {top} L {x - 3} {top + length}" stroke="url(#drop)" stroke-width="{width}" '
                   'stroke-linecap="round"/>\n' for x in xs)


def flakes(points):
    parts = []
    for x, y in points:
        parts.append(f'  <g stroke="#7FC4FF" stroke-width="2" stroke-linecap="round">'
                     f'<path d="M {x} {y - 4} V {y + 4}"/><path d="M {x - 3.5} {y - 2} L {x + 3.5} {y + 2}"/>'
                     f'<path d="M {x - 3.5} {y + 2} L {x + 3.5} {y - 2}"/></g>\n')
    return "".join(parts)


def bolt():
    return '  <path d="M 34 38 L 25 52 H 32 L 28 62 L 41 46 H 34 L 38 38 Z" fill="url(#bolt)"/>\n'


DRAWINGS = {
    "clear-day": ("Clear, day", sun(32, 32, 13)),
    "clear-night": ("Clear, night", moon(30, 32, 17)),
    "mostly-clear-day": ("Mostly sunny", sun(26, 24, 12) + cloud("cloud", 8, 10, 0.62)),
    "mostly-clear-night": ("Mostly clear, night", moon(26, 24, 14) + cloud("cloud", 8, 10, 0.62)),
    "partly-cloudy-day": ("Partly cloudy", sun(24, 22, 11) + cloud("cloud", 4, 4, 0.86)),
    "partly-cloudy-night": ("Partly cloudy, night", moon(24, 22, 13) + cloud("cloud", 4, 4, 0.86)),
    "cloudy": ("Cloudy", cloud("dark", -6, -6, 0.7) + cloud("cloud", 3, 2, 0.95)),
    "fog": ("Fog", cloud("cloud", 0, -6, 0.9)
            + "".join(f'  <path d="M {x1} {y} H {x2}" stroke="#A7B1C2" stroke-width="3.2" stroke-linecap="round"/>\n'
                      for x1, x2, y in ((14, 50, 46), (10, 44, 53), (20, 54, 60)))),
    "drizzle": ("Drizzle", cloud("cloud", 0, -6, 0.95) + drops((24, 34, 44), 48, 5)),
    "rain": ("Rain", cloud("dark", 0, -6, 0.95) + drops((22, 32, 42), 47, 9)),
    "heavy-rain": ("Heavy rain", cloud("storm", 0, -7, 0.95) + drops((18, 27, 36, 45), 46, 11, True)),
    "freezing-rain": ("Freezing rain", cloud("dark", 0, -6, 0.95) + drops((22, 42), 47, 8) + flakes(((32, 53),))),
    "snow": ("Snow", cloud("cloud", 0, -7, 0.95) + flakes(((21, 51), (32, 57), (43, 51)))),
    "showers-day": ("Rain showers", sun(22, 20, 10) + cloud("cloud", 5, 0, 0.82) + drops((28, 38, 48), 50, 7)),
    "showers-night": ("Rain showers, night", moon(22, 20, 12) + cloud("cloud", 5, 0, 0.82)
                      + drops((28, 38, 48), 50, 7)),
    "snow-showers": ("Snow showers", sun(22, 20, 10) + cloud("cloud", 5, 0, 0.82) + flakes(((30, 54), (44, 54)))),
    "thunderstorm": ("Thunderstorm", cloud("storm", 0, -8, 0.95) + bolt() + drops((18, 46), 46, 8)),
}

# Small line glyphs (24 x 24, currentColor through Kirigami's mask): the
# rail and the detail cards.
GLYPH_HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">\n'
              '  <!-- {what}: VeltOS artwork (tools/weather-icons.py). SPDX-License-Identifier: CC-BY-SA-4.0 -->\n'
              '  <g fill="none" stroke="#000" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">\n')
GLYPHS = {
    "glyph-forecast": ("Forecast", '<circle cx="9" cy="8" r="3"/><path d="M9 2.5v1M3.5 8h1M5.1 4.1l.7.7M12.9 4.1l-.7.7"/>'
                       '<path d="M7 20h10a4 4 0 0 0 .4-8 5 5 0 0 0-9.6 1.2A3.4 3.4 0 0 0 7 20z"/>'),
    "glyph-history": ("Historical weather", '<path d="M4 20V4M4 20h16"/><path d="M7 15l4-4 3 3 5-6"/>'),
    "glyph-favorites": ("Favorites", '<path d="M12 3.5l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/>'),
    "glyph-settings": ("Settings", '<circle cx="12" cy="12" r="3"/><path d="M12 2.8l1.6 2.4 2.8-.6.6 2.8 2.4 1.6-1.4 2.5 1.4 2.5-2.4 1.6-.6 2.8-2.8-.6L12 21.2l-1.6-2.4-2.8.6-.6-2.8-2.4-1.6L6 12.5 4.6 10l2.4-1.6.6-2.8 2.8.6z"/>'),
    "glyph-search": ("Search", '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>'),
    "glyph-star": ("Star", '<path d="M12 3.5l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/>'),
    "glyph-star-filled": ("Star, filled", '<path fill="#000" d="M12 3.5l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/>'),
    "glyph-home": ("Home", '<path d="M4 11l8-7 8 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/>'),
    "glyph-pin": ("Location", '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>'),
    "glyph-refresh": ("Refresh", '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5v4h-4"/>'),
    "glyph-air": ("Air quality", '<path d="M3 9h10a3 3 0 1 0-3-3"/><path d="M3 13h15a3 3 0 1 1-3 3"/><path d="M3 17h7"/>'),
    "glyph-wind": ("Wind", '<path d="M3 8h11a2.5 2.5 0 1 0-2.5-2.5"/><path d="M3 12h15a2.5 2.5 0 1 1-2.5 2.5"/><path d="M3 16h8"/>'),
    "glyph-humidity": ("Humidity", '<path d="M12 3.5s6 6.4 6 10.5a6 6 0 0 1-12 0c0-4.1 6-10.5 6-10.5z"/>'),
    "glyph-visibility": ("Visibility", '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>'),
    "glyph-pressure": ("Pressure", '<circle cx="12" cy="12" r="8.5"/><path d="M12 12l4-4"/><path d="M12 5.5v1.5M5.5 12H7M17 12h1.5"/>'),
    "glyph-dewpoint": ("Dew point", '<path d="M10 14.5V5a2 2 0 0 1 4 0v9.5a4 4 0 1 1-4 0z"/><path d="M12 11v6"/>'),
    "glyph-uv": ("UV index", '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>'),
    "glyph-sunrise": ("Sun", '<path d="M7 17a5 5 0 0 1 10 0"/><path d="M3 20h18M12 5v4M4.9 9.9l1.4 1.4M19.1 9.9l-1.4 1.4"/>'),
    "glyph-moon": ("Moon", '<path d="M19 14.5A7.5 7.5 0 1 1 9.5 5a6 6 0 0 0 9.5 9.5z"/>'),
    "glyph-feels": ("Feels like", '<path d="M10 14.5V5a2 2 0 0 1 4 0v9.5a4 4 0 1 1-4 0z"/><path d="M17.5 7h3M17.5 10h2"/>'),
    "glyph-precipitation": ("Precipitation", '<path d="M7 15a4 4 0 0 1 .3-8 5.5 5.5 0 0 1 10.4 1.6A3.3 3.3 0 0 1 17 15"/><path d="M9 18l-1 2.5M13 18l-1 2.5M17 18l-1 2.5"/>'),
    "glyph-drop": ("Chance of precipitation", '<path d="M12 4s5 5.4 5 9a5 5 0 0 1-10 0c0-3.6 5-9 5-9z"/>'),
    "glyph-arrow": ("Wind direction", '<path d="M12 4v16M6.5 14.5L12 20l5.5-5.5"/>'),
    "glyph-close": ("Close", '<path d="M6 6l12 12M18 6L6 18"/>'),
    "glyph-delete": ("Delete", '<path d="M4.5 6.5h15M9.5 6.5V4.5h5v2M6.5 6.5l1 13h9l1-13"/>'),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for name, (what, body) in DRAWINGS.items():
        (OUT / f"{name}.svg").write_text(svg(what, body), encoding="utf-8", newline="\n")
    for name, (what, body) in GLYPHS.items():
        (OUT / f"{name}.svg").write_text(GLYPH_HEAD.format(what=what) + "    " + body + "\n  </g>\n</svg>\n",
                                         encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
