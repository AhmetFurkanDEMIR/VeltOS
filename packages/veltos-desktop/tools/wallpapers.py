"""VeltOS wallpapers: soft, original artwork in the spirit of Windows 11's
desktop pictures (no Microsoft imagery, no logo, no text).

    svg(design, variant) -> SVG text, 3840 x 2160
    DESIGNS: design -> (package id, display name)

Designs, each with a light and a dark variant (Plasma shows
contents/images_dark/ while the colour scheme is dark):

    bloom   the default: translucent petals opening around the centre of
            the screen on a calm gradient
    flow    wide ribbons of colour flowing across the screen
    glow    large soft lights blending into each other
    lake    the first VeltOS wallpaper (tools/bloom.py): a ribbon bloom
            over a lake at sunrise

Every shape is computed here, so builds are reproducible. The generated
artwork is CC-BY-SA-4.0; this code is GPL-3.0-or-later.
"""

import math
import random

import bloom as lake_bloom

W, H = 3840, 2160

DESIGNS = {
    "bloom": ("VeltOS", "VeltOS Bloom"),
    "flow": ("VeltOS-Flow", "VeltOS Flow"),
    "glow": ("VeltOS-Glow", "VeltOS Glow"),
    "lake": ("VeltOS-Lake", "VeltOS Lake"),
}


def _stop(offset, color, opacity=1.0):
    return f'<stop offset="{offset:g}" stop-color="{color}" stop-opacity="{opacity:g}"/>'


def _document(defs, body):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs>{defs}</defs>{body}</svg>\n')


def _backdrop(stops, glows):
    """A diagonal gradient and soft radial lights: (cx, cy, r, colour, opacity)."""
    defs = ['<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
            + "".join(_stop(o, c) for o, c in stops) + "</linearGradient>"]
    body = [f'<rect x="-100" y="-100" width="{W + 200}" height="{H + 200}" fill="url(#bg)"/>']
    for i, (cx, cy, r, colour, opacity) in enumerate(glows):
        defs.append(f'<radialGradient id="light{i}" cx="{cx}" cy="{cy}" r="{r}" gradientUnits="userSpaceOnUse">'
                    f'{_stop(0, colour, opacity)}{_stop(0.45, colour, opacity * 0.45)}{_stop(1, colour, 0)}'
                    '</radialGradient>')
        body.append(f'<rect x="-100" y="-100" width="{W + 200}" height="{H + 200}" fill="url(#light{i})"/>')
    return "".join(defs), "".join(body)


# --- Bloom (default) ----------------------------------------------------------

BLOOM_CENTER = (1960, 1240)
BLOOM_SEED = 20261020
# Rings from the back to the front:
# (petals, length, width, first angle, opacity, gradient id).
BLOOM_RINGS = [
    (8, 1360, 700, 8, 0.48, "ring0"),
    (7, 1100, 600, 30, 0.60, "ring1"),
    (6, 820, 480, 2, 0.72, "ring2"),
    (5, 520, 330, 24, 0.84, "ring3"),
]
BLOOM = {
    "light": {
        "bg": [(0, "#EEF3FB"), (0.5, "#D3E1F7"), (1, "#A9C3EE")],
        "lights": [(1960, 1240, 1800, "#FFFFFF", 0.75), (300, 200, 1500, "#FFFFFF", 0.5)],
        # base (inside the bloom) -> tip, per ring
        "rings": [("#2E62E0", "#BFDCFF"), ("#2557DA", "#A9D0FF"),
                  ("#1F4FD4", "#9CC8FF"), ("#1A47CC", "#CFE6FF")],
        "edge": ("#FFFFFF", 0.35),
        "shadow": ("#0B2A80", 0.16),
        "heart": ("#FFFFFF", 0.85),
    },
    "dark": {
        "bg": [(0, "#0A0F2A"), (0.55, "#0E1844"), (1, "#16255F")],
        "lights": [(1960, 1240, 1700, "#3D6CFF", 0.42), (3500, 2000, 1500, "#5B3FE0", 0.25)],
        "rings": [("#0C2A8E", "#4F8BFF"), ("#0D2E9A", "#5C98FF"),
                  ("#1036A8", "#6AA6FF"), ("#1440B8", "#8CC2FF")],
        "edge": ("#CFE4FF", 0.30),
        "shadow": ("#000318", 0.40),
        "heart": ("#9CC8FF", 0.65),
    },
}


def petal_path(length, width):
    """A petal pointing up from the origin, gently curved to one side."""
    L, w = length, width
    return (f"M 0 0 C {-0.66 * w:.1f} {-0.22 * L:.1f} {-0.50 * w:.1f} {-0.86 * L:.1f} {-0.04 * w:.1f} {-L:.1f} "
            f"C {0.34 * w:.1f} {-0.94 * L:.1f} {0.58 * w:.1f} {-0.34 * L:.1f} 0 0 Z")


def bloom_svg(variant):
    p = BLOOM[variant]
    defs, body = _backdrop(p["bg"], p["lights"])
    defs = [defs,
            '<filter id="petal-shadow" x="-40%" y="-40%" width="180%" height="180%">'
            '<feGaussianBlur stdDeviation="46"/></filter>',
            # Across each petal: a lit side and a shaded side.
            '<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">'
            f'{_stop(0, "#FFFFFF", 0.30)}{_stop(0.45, "#FFFFFF", 0)}{_stop(1, "#001050", 0.18)}</linearGradient>']
    for (base, tip), (_n, _l, _w, _a, _o, gid) in zip(p["rings"], BLOOM_RINGS):
        defs.append(f'<linearGradient id="{gid}" x1="0.5" y1="1" x2="0.5" y2="0">'
                    f'{_stop(0, base)}{_stop(0.55, base, 0.85)}{_stop(1, tip)}</linearGradient>')
    heart, heart_op = p["heart"]
    defs.append('<radialGradient id="heart" cx="0.5" cy="0.5" r="0.5">'
                f'{_stop(0, heart, heart_op)}{_stop(1, heart, 0)}</radialGradient>')
    cx, cy = BLOOM_CENTER
    edge, edge_op = p["edge"]
    shadow, shadow_op = p["shadow"]
    parts = [body]
    rng = random.Random(BLOOM_SEED)
    for count, length, width, first, opacity, gid in BLOOM_RINGS:
        petals, shadows = [], []
        for i in range(count):
            # A little variation, so the bloom looks grown rather than drawn.
            path = petal_path(length * rng.uniform(0.92, 1.06), width * rng.uniform(0.9, 1.08))
            angle = first + i * 360 / count + rng.uniform(-5, 5)
            transform = f"translate({cx} {cy}) rotate({angle:.2f})"
            shadows.append(f'<path d="{path}" transform="{transform}"/>')
            petals.append(
                f'<g transform="{transform}" opacity="{opacity:g}">'
                f'<path d="{path}" fill="url(#{gid})"/>'
                f'<path d="{path}" fill="url(#sheen)"/>'
                f'<path d="{path}" fill="none" stroke="{edge}" stroke-opacity="{edge_op:g}" stroke-width="3"/>'
                '</g>')
        parts.append(f'<g filter="url(#petal-shadow)" fill="{shadow}" opacity="{shadow_op:g}" '
                     f'transform="translate(18 34)">{"".join(shadows)}</g>')
        parts.append("".join(petals))
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="300" fill="url(#heart)"/>')
    return _document("".join(defs), "".join(parts))


# --- Flow -----------------------------------------------------------------------

FLOW = {
    "light": {
        "bg": [(0, "#F5F3FC"), (0.55, "#E4EAFB"), (1, "#CBD8F6")],
        "lights": [(3000, 600, 1600, "#FFFFFF", 0.6)],
        "bands": [("#2FA8F0", "#4F7CFF", "#8A6BFF"), ("#4F7CFF", "#6F5CF0", "#2FA8F0"),
                  ("#7BC4FF", "#4F7CFF", "#5B3FE0"), ("#A9D4FF", "#7D9BFF", "#B3A1FF"),
                  ("#4F7CFF", "#2FA8F0", "#9CC8FF")],
        "opacity": [0.55, 0.5, 0.45, 0.6, 0.35],
        "line": ("#FFFFFF", 0.7),
    },
    "dark": {
        "bg": [(0, "#080B22"), (0.6, "#0E143A"), (1, "#151D52")],
        "lights": [(2600, 1300, 1700, "#3D6CFF", 0.30)],
        "bands": [("#2FA8F0", "#4F7CFF", "#8A6BFF"), ("#3F6BFF", "#6A4FE8", "#2FA8F0"),
                  ("#2A63E6", "#4F7CFF", "#7A5CFF"), ("#5B8DFF", "#3F5FE8", "#8C78FF"),
                  ("#1E8FE0", "#2F5EE6", "#5B3FE0")],
        "opacity": [0.65, 0.55, 0.5, 0.45, 0.4],
        "line": ("#BFD9FF", 0.55),
    },
}


def _wave(y, amplitude, phase, period=W * 0.9):
    """Points of a gentle wave across the screen."""
    points = []
    for i in range(0, 41):
        x = -300 + i * (W + 600) / 40
        points.append((x, y + amplitude * math.sin(2 * math.pi * x / period + phase)
                       + amplitude * 0.35 * math.sin(2 * math.pi * x / (period * 0.47) + phase * 1.7)))
    return points


def _smooth(points):
    """A smooth path through points (Catmull-Rom as cubic Beziers)."""
    d = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d)


def flow_svg(variant):
    p = FLOW[variant]
    defs, body = _backdrop(p["bg"], p["lights"])
    defs = [defs, '<filter id="soften" x="-5%" y="-30%" width="110%" height="160%">'
                  '<feGaussianBlur stdDeviation="10"/></filter>']
    # (centre y, thickness, amplitude, phase, tilt)
    bands = [(1180, 420, 210, 0.4, 260), (1320, 360, 240, 1.3, 180), (1460, 300, 190, 2.2, 120),
             (1060, 220, 260, 3.1, 320), (1620, 260, 160, 4.0, 60)]
    parts = [body]
    line, line_op = p["line"]
    for i, ((cy, thick, amp, phase, tilt), colours, opacity) in enumerate(zip(bands, p["bands"], p["opacity"])):
        defs.append(f'<linearGradient id="band{i}" x1="0" y1="0" x2="1" y2="0">'
                    f'{_stop(0, colours[0])}{_stop(0.5, colours[1])}{_stop(1, colours[2])}</linearGradient>')
        top = [(x, y - tilt * (x / W - 0.5)) for x, y in _wave(cy - thick / 2, amp, phase)]
        bottom = [(x, y - tilt * (x / W - 0.5)) for x, y in _wave(cy + thick / 2, amp * 0.8, phase + 0.5)]
        outline = _smooth(top) + " L " + _smooth(list(reversed(bottom)))[2:] + " Z"
        parts.append(f'<path d="{outline}" fill="url(#band{i})" opacity="{opacity:g}" filter="url(#soften)"/>')
        parts.append(f'<path d="{_smooth(top)}" fill="none" stroke="{line}" stroke-opacity="{line_op * opacity:g}" '
                     'stroke-width="4"/>')
    return _document("".join(defs), "".join(parts))


# --- Glow ------------------------------------------------------------------------

GLOW = {
    "light": {
        "bg": [(0, "#F4F6FC"), (1, "#DCE4F7")],
        "lights": [(2400, 900, 1500, "#7FB2FF", 0.85), (1100, 1500, 1300, "#B49BFF", 0.65),
                   (3300, 1800, 1200, "#6FD0FF", 0.6), (600, 300, 1100, "#FFD9C2", 0.55),
                   (1900, 2100, 900, "#4F7CFF", 0.45)],
    },
    "dark": {
        "bg": [(0, "#05081A"), (1, "#0C1236")],
        "lights": [(2400, 900, 1500, "#2F5EE6", 0.85), (1100, 1500, 1300, "#5B3FE0", 0.7),
                   (3300, 1800, 1200, "#1E8FE0", 0.6), (600, 300, 1100, "#8A3FD0", 0.35),
                   (1900, 2100, 900, "#4F7CFF", 0.5)],
    },
}


def glow_svg(variant):
    p = GLOW[variant]
    defs, body = _backdrop(p["bg"], p["lights"])
    return _document(defs, body)


def svg(design, variant):
    if design == "bloom":
        return bloom_svg(variant)
    if design == "flow":
        return flow_svg(variant)
    if design == "glow":
        return glow_svg(variant)
    if design == "lake":
        return lake_bloom.wallpaper_svg(variant)
    raise ValueError(design)
