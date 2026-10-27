"""Keyboard Lighting's settings and the sign-in restore, without Qt: the
restore at sign-in (`veltos-lighting --restore`) starts only Python and
ends at once on a PC without keyboard lights."""

import configparser
import json
import os
import subprocess
from pathlib import Path

from . import leds

HELPER = "/usr/libexec/veltos/keyboard-light"
SWATCHES = ["#FFFFFF", "#FF3B30", "#FF9500", "#FFCC00", "#34C759", "#00C7BE", "#30B0FF", "#2F5EE6",
            "#5B3FE0", "#AF52DE", "#FF2D92", "#4F7CFF"]


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def kde_value(group, key):
    for path in (config_home() / "kdeglobals", config_home() / "kdedefaults/kdeglobals",
                 Path("/etc/xdg/kdeglobals")):
        parser = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        if parser.has_option(group, key):
            return parser.get(group, key)
    return ""


def dark_mode():
    return kde_value("KDE", "LookAndFeelPackage").endswith(".dark")


def accent():
    parts = [p for p in kde_value("General", "AccentColor").split(",") if p.strip().isdigit()]
    return "#%02X%02X%02X" % tuple(int(p) for p in parts[:3]) if len(parts) >= 3 else ""


def text_scale():
    parts = kde_value("General", "font").split(",")
    try:
        return max(1.0, min(2.25, float(parts[1]) / 10)) if len(parts) > 1 else 1.0
    except ValueError:
        return 1.0


def settings_path():
    return config_home() / "veltos" / "lighting.json"


def load_settings(path=None):
    try:
        data = json.loads(Path(path or settings_path()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(data, path=None):
    path = Path(path or settings_path())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
        return True
    except OSError:
        return False


def helper_command(led, choice, kind, helper=HELPER):
    """The pkexec command that applies `choice` to the light."""
    command = ["pkexec", helper, led["id"]]
    maximum = led["max"]
    level = round(maximum * choice.get("brightness", 100) / 100) if choice.get("on", True) else 0
    if choice.get("on", True) and choice.get("brightness", 100) > 0:
        level = max(1, level)
    command += ["--brightness", str(level)]
    if kind and choice.get("color"):
        command += ["--color", choice["color"], "--effect", choice.get("effect", "static"),
                    "--speed", str(choice.get("speed", 1))]
    return command


def run(command):
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, timeout=30).returncode
    except (OSError, subprocess.SubprocessError):
        return 1


def restore(root=leds.LEDS, runner=run, path=None, accent_color=None):
    """Applies the saved choices at sign-in; True when there was nothing to do
    or everything worked."""
    saved = load_settings(path)
    ok = True
    for led in leds.keyboards(root):
        choice = saved.get(led["id"])
        if not isinstance(choice, dict):
            continue
        choice = dict(choice)
        if choice.get("matchAccent") and led["colorKind"]:
            choice["color"] = (accent_color if accent_color is not None else accent()) or choice.get("color", "")
        ok = runner(helper_command(led, choice, led["colorKind"])) == 0 and ok
    return ok
