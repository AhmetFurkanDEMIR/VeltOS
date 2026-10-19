"""Procedural generator for the VeltOS "Velt Bloom" wallpaper.

    wallpaper_svg("light" | "dark") -> SVG text (3840x2160)

Scene, back to front: soft sky gradient, sunrise glow, misty mountains over a
calm lake (with reflection), a large bloom of folded blue ribbons in the
lower right. No logo or text, as on Windows 11. Every shape is
computed here from a fixed seed, so builds are reproducible and the artwork
is original VeltOS work (no third-party imagery).

The generated artwork is CC-BY-SA-4.0; this code is GPL-3.0-or-later.
"""

import math
import random

W, H = 3840, 2160
HORIZON = 1560
BLOOM_CENTER = (2640, 2400)
SEED = 20261019

PALETTES = {
    "light": {
        "sky": ["#EEF3FB", "#CADCF6", "#8DB1EE", "#5A88DE"],
        "glow": ("#FFE4BF", 0.95),
        "haze": ("#FFFFFF", 0.5),
        "ridge_far": ("#A3BAE6", "#DAE5F7"),
        "ridge_near": ("#86A2DA", "#CFDCF3"),
        "lake": ("#DDE7F7", "#AFC6EE"),
        "horizon": ("#FFFFFF", 0.85),
        "bloom_glow": ("#A9CCFF", 0.6),
        "shadow": ("#04145E", 0.55),
        # Per layer (back to front): lit outside of the fold, shaded inside.
        "petal": [(0, "#051672"), (0.58, "#0B36C4"), (0.8, "#2369EE"),
                  (0.94, "#4FA6FF"), (1, "#9AD8FF")],
        "rolled": ("#B9E6FF", "#3E8CFF"),
        "rim": ("#FFFFFF", 0.8),
    },
    "dark": {
        "sky": ["#060A1E", "#0A1436", "#132766", "#1C3A96"],
        "glow": ("#6A5CFF", 0.40),
        "haze": ("#4F7CFF", 0.10),
        "ridge_far": ("#1A2556", "#26366F"),
        "ridge_near": ("#121B45", "#1F2D60"),
        "lake": ("#16225A", "#090F2C"),
        "horizon": ("#8FB2FF", 0.45),
        "bloom_glow": ("#3D6CFF", 0.45),
        "shadow": ("#00030E", 0.6),
        "petal": [(0, "#020940"), (0.58, "#08249A"), (0.8, "#1C58E2"),
                  (0.94, "#3C90FF"), (1, "#7CC4FF")],
        "rolled": ("#A9DCFF", "#2F74F0"),
        "rim": ("#CFEBFF", 0.65),
    },
}

# Ribbon layers from the back (largest) to the front (smallest):
# (count, length, width, first angle, last angle); angle 0 points up.
LAYERS = [
    (9, 1850, 860, -128, 42),
    (8, 1580, 760, -118, 46),
    (8, 1300, 640, -110, 52),
    (7, 1010, 520, -102, 54),
    (6, 730, 400, -94, 52),
    (5, 470, 270, -86, 48),
]


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _poly(points):
    return " ".join(f"{x:.1f} {y:.1f}" for x, y in points)


def ribbon_paths(length, width):
    """One bloom petal, base at the origin, pointing up (negative y).

    Returns (body, rolled_rim, rim_line): the petal outline, the crescent
    of its edge rolled over towards the viewer, and the lit edge line.
    """
    L, Wd = length, width
    body = (f"M 0 0 "
            f"C {-0.62 * Wd:.1f} {-0.12 * L:.1f} {-0.80 * Wd:.1f} {-0.78 * L:.1f} {-0.10 * Wd:.1f} {-L:.1f} "
            f"C {0.34 * Wd:.1f} {-1.12 * L:.1f} {0.86 * Wd:.1f} {-0.88 * L:.1f} {0.66 * Wd:.1f} {-0.56 * L:.1f} "
            f"C {0.54 * Wd:.1f} {-0.30 * L:.1f} {0.26 * Wd:.1f} {-0.10 * L:.1f} 0 0 Z")
    rolled = (f"M {-0.10 * Wd:.1f} {-L:.1f} "
              f"C {0.34 * Wd:.1f} {-1.12 * L:.1f} {0.86 * Wd:.1f} {-0.88 * L:.1f} {0.66 * Wd:.1f} {-0.56 * L:.1f} "
              f"C {0.60 * Wd:.1f} {-0.74 * L:.1f} {0.28 * Wd:.1f} {-0.98 * L:.1f} {-0.10 * Wd:.1f} {-L:.1f} Z")
    rim = (f"M {-0.10 * Wd:.1f} {-L:.1f} "
           f"C {0.34 * Wd:.1f} {-1.12 * L:.1f} {0.86 * Wd:.1f} {-0.88 * L:.1f} {0.66 * Wd:.1f} {-0.56 * L:.1f}")
    return body, rolled, rim


def layout():
    """Deterministic list of ribbons: (layer, angle, length, width, mirrored)."""
    rng = random.Random(SEED)
    ribbons = []
    for layer, (count, length, width, first, last) in enumerate(LAYERS):
        step = (last - first) / max(count - 1, 1)
        for i in range(count):
            ribbons.append((
                layer,
                first + i * step + rng.uniform(-0.25, 0.25) * step,
                length * rng.uniform(0.92, 1.06),
                width * rng.uniform(0.9, 1.08),
                rng.random() < 0.4,
            ))
    return ribbons


def _stop(offset, color, opacity=1.0):
    return f'<stop offset="{offset}" stop-color="{color}" stop-opacity="{opacity}"/>'


def defs(p):
    sky = "".join(_stop(f"{i / (len(p['sky']) - 1):.2f}", c) for i, c in enumerate(p["sky"]))
    glow, glow_op = p["glow"]
    haze, haze_op = p["haze"]
    bloom_glow, bloom_glow_op = p["bloom_glow"]
    out = [
        f'<linearGradient id="sky" x1="0" y1="0" x2="{W}" y2="{HORIZON}" gradientUnits="userSpaceOnUse">{sky}</linearGradient>',
        f'<radialGradient id="glow" cx="260" cy="{HORIZON - 40}" r="1800" gradientUnits="userSpaceOnUse">'
        f'{_stop(0, glow, glow_op)}{_stop(0.4, glow, round(glow_op * 0.45, 2))}{_stop(1, glow, 0)}</radialGradient>',
        f'<radialGradient id="haze" cx="1200" cy="1300" r="1500" gradientUnits="userSpaceOnUse">'
        f'{_stop(0, haze, haze_op)}{_stop(1, haze, 0)}</radialGradient>',
        f'<radialGradient id="bloom-glow" cx="{BLOOM_CENTER[0] - 250}" cy="{BLOOM_CENTER[1] - 900}" r="1800" gradientUnits="userSpaceOnUse">'
        f'{_stop(0, bloom_glow, bloom_glow_op)}{_stop(1, bloom_glow, 0)}</radialGradient>',
        # Darkens each ribbon towards its base, where it disappears into the bloom.
        f'<linearGradient id="depth" x1="0" y1="1" x2="0" y2="0">'
        f'{_stop(0, "#020C40", 0.55)}{_stop(0.45, "#020C40", 0)}{_stop(1, "#020C40", 0)}</linearGradient>',
        '<filter id="soft-shadow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="52"/></filter>',
        '<filter id="mist" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>',
        '<filter id="soft-line" x="-5%" y="-500%" width="110%" height="1100%"><feGaussianBlur stdDeviation="6"/></filter>',
    ]
    for name in ("ridge_far", "ridge_near", "lake"):
        top, bottom = p[name]
        y1, y2 = (1250, HORIZON) if name != "lake" else (HORIZON, H + 200)
        out.append(f'<linearGradient id="{name}" x1="0" y1="{y1}" x2="0" y2="{y2}" gradientUnits="userSpaceOnUse">'
                   f'{_stop(0, top)}{_stop(1, bottom)}</linearGradient>')
    for layer, (_count, length, *_rest) in enumerate(LAYERS):
        # Radial shading from the petal base (the bloom centre) to its rim:
        # deep navy inside the bloom, bright azure at the edge.
        stops = "".join(_stop(o, c) for o, c in p["petal"])
        out.append(f'<radialGradient id="petal{layer}" cx="0" cy="0" r="{length * 1.04:.0f}" '
                   f'gradientUnits="userSpaceOnUse">{stops}</radialGradient>')
    hi, lo = p["rolled"]
    out += [
        # Across the petal: a lit side and a shaded side, for a curved look.
        '<linearGradient id="fold" x1="0" y1="0" x2="1" y2="0">'
        f'{_stop(0, "#FFFFFF", 0.24)}{_stop(0.42, "#FFFFFF", 0)}'
        f'{_stop(0.75, "#00104F", 0.08)}{_stop(1, "#00104F", 0.3)}</linearGradient>',
        f'<linearGradient id="rolled" x1="0" y1="0" x2="1" y2="1">{_stop(0, hi)}{_stop(1, lo)}</linearGradient>',
    ]
    return "<defs>" + "".join(out) + "</defs>"


def landscape(p):
    far = (f"M -2000 {HORIZON} L -200 {HORIZON} C 200 1430, 430 1360, 700 1380 "
           f"C 960 1400, 1110 1300, 1360 1334 C 1610 1368, 1790 1496, 2100 {HORIZON} Z")
    near = (f"M -2000 {HORIZON} L -200 {HORIZON} C 110 1494, 320 1450, 540 1458 "
            f"C 790 1468, 940 1518, 1280 {HORIZON} Z")
    horizon_color, horizon_op = p["horizon"]
    return (
        f'<rect x="-2000" y="{HORIZON}" width="{W + 4000}" height="{H + 2000 - HORIZON}" fill="url(#lake)"/>'
        f'<g opacity="0.3" filter="url(#mist)" transform="translate(0 {2 * HORIZON}) scale(1 -1)">'
        f'<path d="{far}" fill="url(#ridge_far)"/><path d="{near}" fill="url(#ridge_near)"/></g>'
        f'<path d="{far}" fill="url(#ridge_far)" opacity="0.85"/>'
        f'<path d="{near}" fill="url(#ridge_near)" opacity="0.9"/>'
        f'<rect x="-2000" y="{HORIZON - 4}" width="{W + 4000}" height="8" fill="{horizon_color}" '
        f'opacity="{horizon_op}" filter="url(#soft-line)"/>'
    )


def bloom(p, with_glow=True):
    cx, cy = BLOOM_CENTER
    shadow_color, shadow_op = p["shadow"]
    rim_color, rim_op = p["rim"]
    parts = []
    if with_glow:
        parts.append(f'<rect x="-2000" y="-2000" width="{W + 4000}" height="{H + 4000}" fill="url(#bloom-glow)"/>')
    ribbons = layout()
    for layer in range(len(LAYERS)):
        shadows, group = [], []
        for lay, angle, length, width, mirrored in ribbons:
            if lay != layer:
                continue
            body, rolled, rim = ribbon_paths(length, width)
            transform = f"translate({cx} {cy}) rotate({angle:.2f})" + (" scale(-1 1)" if mirrored else "")
            shadows.append(f'<path d="{body}" transform="{transform}"/>')
            group.append(
                f'<g transform="{transform}">'
                f'<path d="{body}" fill="url(#petal{layer})"/>'
                f'<path d="{body}" fill="url(#fold)"/>'
                f'<path d="{rolled}" fill="url(#rolled)" opacity="0.92"/>'
                f'<path d="{rim}" fill="none" stroke="{rim_color}" stroke-opacity="{rim_op}" '
                f'stroke-width="{max(3.0, width / 160):.1f}" stroke-linecap="round"/>'
                f'</g>')
        # Each layer casts a soft shadow onto the layers behind it.
        parts.append(f'<g filter="url(#soft-shadow)" fill="{shadow_color}" opacity="{shadow_op}" '
                     f'transform="translate(30 46)">{"".join(shadows)}</g>')
        parts.append("".join(group))
    return "".join(parts)


def wallpaper_svg(variant):
    p = PALETTES[variant]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'{defs(p)}'
        f'<rect x="-2000" y="-2000" width="{W + 4000}" height="{H + 4000}" fill="url(#sky)"/>'
        f'<rect x="-2000" y="-2000" width="{W + 4000}" height="{H + 4000}" fill="url(#glow)"/>'
        f'<rect x="-2000" y="-2000" width="{W + 4000}" height="{H + 4000}" fill="url(#haze)"/>'
        f'{landscape(p)}{bloom(p)}'
        '</svg>\n'
    )


def bloom_only_svg(variant, size=1024):
    """The ribbon bloom alone on a transparent square (splash/installer art)."""
    p = PALETTES[variant]
    cx, cy = BLOOM_CENTER
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{cx - 2000} {cy - 2150} 4000 4000">{defs(p)}{bloom(p, with_glow=False)}</svg>\n'
    )
