"""Screen capture and picture work of VeltOS Snipping Tool.

On Wayland KWin lets only programs it trusts take screenshots (its
org.kde.KWin.ScreenShot2 interface is restricted to programs whose desktop
entry asks for it). Spectacle, KDE's screenshot program, is one of them:
VeltOS Snipping Tool asks it for a picture of the whole desktop without
showing its window (`capture_command`) and does the rest itself — freeze
the screen, let the user pick a rectangle, a window, the full screen or a
freeform shape, then crop — like Windows' Snipping Tool.

The window frames for "Window" mode come from a small KWin script that
sends the open windows of the current desktop back over D-Bus
(`window_script`).
"""

import json
import math
import os
import re
from pathlib import Path

# Windows 11 names snips "Screenshot 2026-10-20 103015.png".
NAME_FORMAT = "Screenshot %Y-%m-%d %H%M%S"


def capture_command(path):
    """Spectacle: whole desktop, no window, no notification, into `path`."""
    return ["spectacle", "--background", "--nonotify", "--fullscreen", "--output", str(path)]


def pictures_dir(home=None, config_home=None):
    """The user's Pictures folder (xdg-user-dirs), e.g. ~/Resimler in Turkish."""
    home = Path(home or Path.home())
    config_home = Path(config_home or os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    try:
        text = (config_home / "user-dirs.dirs").read_text(encoding="utf-8")
    except OSError:
        text = ""
    match = re.search(r'^XDG_PICTURES_DIR="([^"]*)"', text, re.MULTILINE)
    if match:
        value = match.group(1).replace("$HOME", str(home))
        if value.strip("/") and Path(value) != home:
            return Path(value)
    return home / "Pictures"


def screenshots_dir(home=None, config_home=None):
    return pictures_dir(home, config_home) / "Screenshots"


def unique_path(directory, now):
    """A new file name in `directory` for a snip taken at `now`."""
    base = now.strftime(NAME_FORMAT)
    path = Path(directory) / f"{base}.png"
    number = 2
    while path.exists():
        path = Path(directory) / f"{base} ({number}).png"
        number += 1
    return path


# --- Windows for "Window" mode ------------------------------------------------------

def window_script(service, path, interface):
    """KWin script that sends the frames of the visible windows of the
    current desktop, bottom to top, as JSON to `service`."""
    return f"""// VeltOS Snipping Tool: windows for "Window" mode (generated).
var shown = [];
var stack = workspace.stackingOrder;
for (var i = 0; i < stack.length; ++i) {{
    var w = stack[i];
    if (!(w.normalWindow || w.dialog) || w.minimized || w.hidden) {{
        continue;
    }}
    if (w.desktops.length > 0 && w.desktops.indexOf(workspace.currentDesktop) < 0) {{
        continue;
    }}
    var g = w.frameGeometry;
    shown.push({{x: g.x, y: g.y, width: g.width, height: g.height, caption: w.caption}});
}}
callDBus("{service}", "{path}", "{interface}", "setWindows", JSON.stringify(shown));
"""


def parse_windows(text):
    """Window frames from the KWin script's JSON (bad entries are dropped)."""
    try:
        data = json.loads(text)
    except ValueError:
        return []
    windows = []
    for item in data if isinstance(data, list) else []:
        try:
            frame = {key: int(round(float(item[key]))) for key in ("x", "y", "width", "height")}
        except (KeyError, TypeError, ValueError):
            continue
        if frame["width"] > 0 and frame["height"] > 0:
            frame["caption"] = str(item.get("caption", ""))
            windows.append(frame)
    return windows


def window_at(windows, x, y):
    """Index of the topmost window (list is bottom to top) at x, y, or -1."""
    for index in range(len(windows) - 1, -1, -1):
        w = windows[index]
        if w["x"] <= x < w["x"] + w["width"] and w["y"] <= y < w["y"] + w["height"]:
            return index
    return -1


# --- Pictures (Qt) ------------------------------------------------------------------

def clamp_rect(x, y, width, height, image_width, image_height):
    """Integer rectangle inside the picture (None if nothing is left)."""
    left = max(0, int(math.floor(x)))
    top = max(0, int(math.floor(y)))
    right = min(image_width, int(math.ceil(x + width)))
    bottom = min(image_height, int(math.ceil(y + height)))
    if right - left < 1 or bottom - top < 1:
        return None
    return left, top, right - left, bottom - top


def crop(image, x, y, width, height):
    """Part of a QImage (picture pixels); None for an empty selection."""
    rect = clamp_rect(x, y, width, height, image.width(), image.height())
    if rect is None:
        return None
    return image.copy(*rect)


def freeform(image, points):
    """The part of `image` inside the polygon `points` ([x, y, x, y, ...]
    in picture pixels): its bounding box, transparent outside the shape."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QImage, QPainter, QPainterPath, QPolygonF

    pairs = [(points[i], points[i + 1]) for i in range(0, len(points) - 1, 2)]
    if len(pairs) < 3:
        return None
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    rect = clamp_rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys), image.width(), image.height())
    if rect is None:
        return None
    left, top, width, height = rect
    result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    result.fill(Qt.GlobalColor.transparent)
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(px - left, py - top) for px, py in pairs]))
    path.closeSubpath()
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setClipPath(path)
    painter.drawImage(0, 0, image, left, top, width, height)
    painter.end()
    return result


HIGHLIGHTER_OPACITY = 0.45


def compose(image, strokes):
    """`image` with the pen and highlighter strokes drawn on it. A stroke is
    {"tool": "pen"|"highlighter", "color": "#rrggbb", "width": px,
    "points": [x, y, x, y, ...]} in picture pixels."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen

    result = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    if not strokes:
        return result
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    for stroke in strokes:
        points = stroke.get("points") or []
        pairs = [QPointF(points[i], points[i + 1]) for i in range(0, len(points) - 1, 2)]
        if not pairs:
            continue
        highlighter = stroke.get("tool") == "highlighter"
        pen = QPen(QColor(stroke.get("color", "#000000")))
        pen.setWidthF(float(stroke.get("width", 4)))
        pen.setCapStyle(Qt.PenCapStyle.FlatCap if highlighter else Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setOpacity(HIGHLIGHTER_OPACITY if highlighter else 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if len(pairs) == 1:
            painter.drawPoint(pairs[0])
            continue
        path = QPainterPath(pairs[0])
        for point in pairs[1:]:
            path.lineTo(point)
        painter.drawPath(path)
    painter.end()
    return result


def _segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def stroke_hit(stroke, x, y, radius):
    """True if the eraser at x, y (radius in picture pixels) touches the
    stroke. Windows' eraser removes whole strokes."""
    points = stroke.get("points") or []
    reach = radius + float(stroke.get("width", 4)) / 2
    if len(points) == 2:
        return math.hypot(points[0] - x, points[1] - y) <= reach
    for i in range(0, len(points) - 3, 2):
        if _segment_distance(x, y, points[i], points[i + 1], points[i + 2], points[i + 3]) <= reach:
            return True
    return False
