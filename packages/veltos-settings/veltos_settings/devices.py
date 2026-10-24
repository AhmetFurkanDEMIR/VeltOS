"""Talk to the system for the built-in Settings pages.

Every class runs standard command-line tools (nmcli, bluetoothctl, pactl,
kscreen-doctor, timedatectl, Plasma's apply tools) through `run`, parses
their output and returns plain data for QML. Tests pass a fake runner.
Nothing here needs root: where the system wants the administrator password
(time zone, automatic time), polkit asks for it.

The calls can take seconds (a Wi-Fi scan, connecting), so app.py runs them
off the UI thread.
"""

import datetime
import json
import os
import re
import subprocess
import time
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9
    ZoneInfo = None


def run(command, timeout=20, input=None):
    """Run a command; return (exit code, stdout). Never raises for missing
    tools or timeouts: Settings must keep working on any machine. `input`
    goes to its standard input (data that must not show in `ps`)."""
    try:
        if input is None:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                    stdin=subprocess.DEVNULL)
        else:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                    input=input)
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def split_terse(line):
    """Split one line of `nmcli -t` output (":" separated, "\\:" escaped)."""
    fields, current, escaped = [], "", False
    for char in line:
        if escaped:
            current += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append(current)
            current = ""
        else:
            current += char
    fields.append(current)
    return fields


def terse_lines(code, out, minimum):
    if code != 0:
        return []
    return [f for f in (split_terse(line) for line in out.splitlines()) if len(f) >= minimum]


# --- Wi-Fi and network ------------------------------------------------------------------

NM_BUS = "org.freedesktop.NetworkManager"
NM_PATH = "/org/freedesktop/NetworkManager"
NM_DEVICE_WIFI = 2                                  # NMDeviceType
NM_DEVICE_DISCONNECTED, NM_DEVICE_NEED_AUTH = 30, 60  # NMDeviceState
NM_ACTIVE_ACTIVATED, NM_ACTIVE_DEACTIVATED = 2, 4     # NMActiveConnectionState


def nm_add_and_activate(ssid, key, key_mgmt, timeout=90):
    """Create a Wi-Fi connection with its key and start it, through
    NetworkManager's D-Bus API (AddAndActivateConnection). True once it is
    connected; on a wrong key the new connection is deleted again, so the
    password agents' prompts that NetworkManager would start are cancelled.
    Uses GLib's D-Bus client (python3-gi), already part of the system."""
    try:
        from gi.repository import Gio, GLib
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    except Exception:  # no GLib bindings or no system bus
        return False

    def call(path, interface, method, args, reply):
        return bus.call_sync(NM_BUS, path, interface, method, args, GLib.VariantType(reply),
                             Gio.DBusCallFlags.NONE, 120000, None).unpack()

    def prop(path, interface, name):
        return call(path, "org.freedesktop.DBus.Properties", "Get",
                    GLib.Variant("(ss)", (interface, name)), "(v)")[0]

    try:
        device = next((path for path in call(NM_PATH, NM_BUS, "GetDevices", None, "(ao)")[0]
                       if prop(path, NM_BUS + ".Device", "DeviceType") == NM_DEVICE_WIFI
                       and prop(path, NM_BUS + ".Device", "State") >= NM_DEVICE_DISCONNECTED), None)
        if device is None:
            return False
        settings = {
            "connection": {"id": GLib.Variant("s", ssid), "type": GLib.Variant("s", "802-11-wireless")},
            "802-11-wireless": {"ssid": GLib.Variant("ay", ssid.encode("utf-8")),
                                "mode": GLib.Variant("s", "infrastructure")},
            "802-11-wireless-security": {"key-mgmt": GLib.Variant("s", key_mgmt),
                                         "psk": GLib.Variant("s", key)},
        }
        connection, active = call(NM_PATH, NM_BUS, "AddAndActivateConnection",
                                  GLib.Variant("(a{sa{sv}}oo)", (settings, device, "/")), "(oo)")
    except GLib.Error:
        return False   # not allowed (polkit), NetworkManager not running, ...

    ok = False
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            # NetworkManager passes "need-auth" once without a reason while
            # it checks that the key exists; with a reason (the supplicant
            # disconnected, ...) the key did not work.
            state, reason = prop(device, NM_BUS + ".Device", "StateReason")
            if state == NM_DEVICE_NEED_AUTH and reason != 0:
                break
            state = prop(active, NM_BUS + ".Connection.Active", "State")
            if state == NM_ACTIVE_ACTIVATED:
                ok = True
                break
            if state == NM_ACTIVE_DEACTIVATED:
                break
            time.sleep(0.2)
    except GLib.Error:
        pass   # the attempt ended and its object is gone
    if not ok:
        try:
            call(connection, NM_BUS + ".Settings.Connection", "Delete", None, "()")
        except GLib.Error:
            pass
    return ok


class Network:
    def __init__(self, runner=run, activate=None):
        self.run = runner
        self.activate = activate or nm_add_and_activate

    def devices(self):
        code, out = self.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"])
        return [{"device": f[0], "type": f[1], "state": f[2], "connection": f[3]}
                for f in terse_lines(code, out, 4) if f[1] in ("wifi", "ethernet")]

    def wifi_enabled(self):
        code, out = self.run(["nmcli", "-t", "-f", "WIFI", "radio"])
        return code == 0 and out.strip() == "enabled"

    def set_wifi(self, enabled):
        return self.run(["nmcli", "radio", "wifi", "on" if enabled else "off"])[0] == 0

    def connection(self, devices=None):
        """The connection the PC uses now: {"type", "name"}, or {}."""
        for device in self.devices() if devices is None else devices:
            if device["state"] == "connected":
                return {"type": device["type"], "name": device["connection"]}
        return {}

    def saved(self):
        """Saved Wi-Fi connections: {SSID: connection UUID}."""
        code, out = self.run(["nmcli", "-t", "-f", "UUID,TYPE", "connection", "show"])
        result = {}
        for uuid, kind, *_ in terse_lines(code, out, 2):
            if kind != "802-11-wireless":
                continue
            code, value = self.run(["nmcli", "-t", "-g", "802-11-wireless.ssid", "connection",
                                    "show", "uuid", uuid])
            ssid = split_terse(value.strip())[0] if code == 0 else ""
            if ssid:
                result.setdefault(ssid, uuid)
        return result

    def networks(self, rescan=False):
        """Visible Wi-Fi networks, the connected one first, then by signal;
        one entry per name."""
        code, out = self.run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi",
                              "list", "--rescan", "yes" if rescan else "auto"], timeout=40)
        best = {}
        for in_use, ssid, signal, security, *_ in terse_lines(code, out, 4):
            if not ssid:
                continue  # hidden network
            security = security.strip()
            entry = {"ssid": ssid, "signal": int(signal) if signal.isdigit() else 0,
                     "security": "" if security in ("", "--") else security,
                     "active": in_use == "*"}
            entry["secure"] = entry["security"] != ""
            entry["enterprise"] = "802.1X" in entry["security"]
            known = best.get(ssid)
            if known is None or entry["active"] or (not known["active"] and entry["signal"] > known["signal"]):
                best[ssid] = entry
        saved = self.saved() if best else {}
        result = sorted(best.values(), key=lambda n: (not n["active"], -n["signal"], n["ssid"].lower()))
        for network in result:
            network["saved"] = network["ssid"] in saved
        return result

    def connect(self, ssid, password="", security=""):
        """Connect to a network. A saved network uses its saved key; an open
        network needs none. A new key goes to NetworkManager inside the
        D-Bus request that creates the connection: it never appears on a
        command line (other users could read it there), and no password
        agent (with its "wallet" prompts) is asked for it."""
        saved = self.saved()
        if ssid in saved:
            return self.run(["nmcli", "connection", "up", "uuid", saved[ssid]], timeout=90)[0] == 0
        if not password:
            return self.run(["nmcli", "device", "wifi", "connect", ssid], timeout=90)[0] == 0
        key_mgmt = "sae" if "WPA3" in security and "WPA2" not in security else "wpa-psk"
        return self.activate(ssid, password, key_mgmt)

    def disconnect(self):
        """Disconnect Wi-Fi; like Windows, the PC does not reconnect on its
        own until the user connects again."""
        ok = True
        for device in self.devices():
            if device["type"] == "wifi" and device["state"] == "connected":
                ok = self.run(["nmcli", "device", "disconnect", device["device"]])[0] == 0 and ok
        return ok

    def forget(self, ssid):
        uuid = self.saved().get(ssid)
        return uuid is not None and self.run(["nmcli", "connection", "delete", "uuid", uuid])[0] == 0

    def state(self, rescan=False):
        devices = self.devices()
        available = any(d["type"] == "wifi" for d in devices)
        enabled = available and self.wifi_enabled()
        return {"available": available, "enabled": enabled,
                "connection": self.connection(devices),
                "networks": self.networks(rescan) if enabled else []}


# --- Bluetooth -----------------------------------------------------------------------------

BLUETOOTH_SYSFS = Path("/sys/class/bluetooth")


class Bluetooth:
    def __init__(self, runner=run):
        self.run = runner

    def powered(self):
        code, out = self.run(["bluetoothctl", "show"], timeout=8)
        return code == 0 and re.search(r"^\s*Powered:\s*yes", out, re.M) is not None

    def available(self):
        # Without an adapter bluetoothd does not run and bluetoothctl waits
        # for it: ask the kernel first.
        if BLUETOOTH_SYSFS.is_dir() and not any(BLUETOOTH_SYSFS.glob("hci*")):
            return False
        code, out = self.run(["bluetoothctl", "list"], timeout=8)
        return code == 0 and "Controller" in out

    def set_powered(self, on):
        return self.run(["bluetoothctl", "power", "on" if on else "off"])[0] == 0

    def devices(self):
        code, out = self.run(["bluetoothctl", "devices", "Paired"])
        result = []
        for line in out.splitlines() if code == 0 else []:
            match = re.match(r"Device ([0-9A-Fa-f:]{17}) (.+)", line.strip())
            if not match:
                continue
            mac, name = match.groups()
            _, info = self.run(["bluetoothctl", "info", mac])
            icon = re.search(r"^\s*Icon:\s*(\S+)", info, re.M)
            battery = re.search(r"^\s*Battery Percentage:.*\((\d+)\)", info, re.M)
            result.append({"mac": mac, "name": name,
                           "connected": re.search(r"^\s*Connected:\s*yes", info, re.M) is not None,
                           "icon": icon.group(1) if icon else "bluetooth",
                           "battery": int(battery.group(1)) if battery else -1})
        return sorted(result, key=lambda d: (not d["connected"], d["name"].lower()))

    def connect(self, mac, on=True):
        return self.run(["bluetoothctl", "connect" if on else "disconnect", mac], timeout=40)[0] == 0

    def remove(self, mac):
        return self.run(["bluetoothctl", "remove", mac])[0] == 0

    def discover(self, seconds=10):
        """Devices in range that are not paired yet (Add a device):
        scan for a while, then list what bluetoothd found."""
        self.run(["bluetoothctl", "--timeout", str(seconds), "scan", "on"], timeout=seconds + 10)
        code, out = self.run(["bluetoothctl", "devices"])
        paired = {d["mac"] for d in self.devices()}
        found = []
        for line in out.splitlines() if code == 0 else []:
            match = re.match(r"Device ([0-9A-Fa-f:]{17}) (.+)", line.strip())
            if not match or match.group(1) in paired:
                continue
            mac, name = match.groups()
            # Nameless devices show their address with dashes as a name.
            if name.replace("-", ":").upper() == mac.upper():
                continue
            _, info = self.run(["bluetoothctl", "info", mac])
            icon = re.search(r"^\s*Icon:\s*(\S+)", info, re.M)
            found.append({"mac": mac, "name": name, "icon": icon.group(1) if icon else "bluetooth"})
        return sorted(found, key=lambda d: d["name"].lower())

    def pair(self, mac):
        """Pair, trust and connect (Plasma's Bluetooth agent asks for PIN
        confirmation where a device needs it)."""
        if self.run(["bluetoothctl", "pair", mac], timeout=60)[0] != 0:
            return False
        self.run(["bluetoothctl", "trust", mac])
        self.connect(mac, True)
        return True

    def state(self):
        available = self.available()
        powered = available and self.powered()
        return {"available": available, "powered": powered,
                "devices": self.devices() if available else []}


# --- Sound -----------------------------------------------------------------------------------

class Sound:
    def __init__(self, runner=run):
        self.run = runner

    def _devices(self, kind):
        code, out = self.run(["pactl", "--format=json", "list", kind])
        try:
            items = json.loads(out) if code == 0 else []
        except ValueError:
            items = []
        _, default = self.run(["pactl", "get-default-" + kind[:-1]])
        result = []
        for item in items if isinstance(items, list) else []:
            name = item.get("name", "")
            if kind == "sources" and (name.endswith(".monitor") or item.get("monitor_source") == ""
                                      and "monitor" in item.get("properties", {}).get("device.class", "")):
                continue  # what a speaker plays, not a microphone
            percents = [int(str(v.get("value_percent", "0")).rstrip("%") or 0)
                        for v in item.get("volume", {}).values() if isinstance(v, dict)]
            result.append({"name": name, "description": item.get("description") or name,
                           "volume": max(percents, default=0), "muted": bool(item.get("mute")),
                           "default": name == default.strip()})
        result.sort(key=lambda d: not d["default"])
        return result

    def state(self):
        return {"outputs": self._devices("sinks"), "inputs": self._devices("sources")}

    @staticmethod
    def _target(kind):
        if kind not in ("sink", "source"):
            raise ValueError(kind)
        return "@DEFAULT_SINK@" if kind == "sink" else "@DEFAULT_SOURCE@"

    def set_default(self, kind, name):
        self._target(kind)
        return self.run(["pactl", "set-default-" + kind, name])[0] == 0

    def set_volume(self, kind, percent):
        percent = max(0, min(100, int(percent)))
        return self.run(["pactl", f"set-{kind}-volume", self._target(kind), f"{percent}%"])[0] == 0

    def set_muted(self, kind, muted):
        return self.run(["pactl", f"set-{kind}-mute", self._target(kind), "1" if muted else "0"])[0] == 0


# --- Display ---------------------------------------------------------------------------------

SCALES = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5]


class Display:
    def __init__(self, runner=run):
        self.run = runner

    def state(self):
        code, out = self.run(["kscreen-doctor", "--json"])
        try:
            data = json.loads(out) if code == 0 else {}
        except ValueError:
            data = {}
        result = []
        for output in data.get("outputs", []) if isinstance(data, dict) else []:
            if not output.get("connected") or not output.get("enabled"):
                continue
            current_id = str(output.get("currentModeId", ""))
            # One entry per resolution: its highest refresh rate (the current
            # mode for the current resolution).
            by_size = {}
            current = None
            for mode in output.get("modes", []):
                size = mode.get("size", {})
                key = (size.get("width") or 0, size.get("height") or 0)
                if not all(key):
                    continue
                entry = {"id": str(mode.get("id")), "width": key[0], "height": key[1],
                         "rate": float(mode.get("refreshRate") or 0),
                         "label": f"{key[0]} × {key[1]}"}
                if entry["id"] == current_id:
                    current = entry
                known = by_size.get(key)
                if known is None or (known["id"] != current_id and
                                     (entry["id"] == current_id or entry["rate"] > known["rate"])):
                    by_size[key] = entry
            modes = sorted(by_size.values(), key=lambda m: (-m["width"], -m["height"]))
            preferred = [str(i) for i in output.get("preferredModes", [])]
            for mode in modes:
                mode["recommended"] = mode["id"] in preferred
            scale = round(float(output.get("scale") or 1.0), 2)
            result.append({"id": output.get("id"), "name": output.get("name", ""),
                           "scale": scale, "scales": sorted(set(SCALES) | {scale}), "modes": modes,
                           "currentMode": current["id"] if current else "",
                           "currentLabel": current["label"] if current else ""})
        return {"outputs": result}

    def set_scale(self, output_id, scale):
        return self.run(["kscreen-doctor", f"output.{int(output_id)}.scale.{float(scale):g}"])[0] == 0

    def set_mode(self, output_id, mode_id):
        if not re.fullmatch(r"[\w.@-]+", str(mode_id)):
            return False
        return self.run(["kscreen-doctor", f"output.{int(output_id)}.mode.{mode_id}"])[0] == 0


# --- Personalization ---------------------------------------------------------------------------

WALLPAPER_DIRS = [Path("/usr/share/wallpapers")]
# KDE's own default picture (installed with Plasma) is not offered; the
# VeltOS pictures and any the user or other packages add are.
HIDDEN_WALLPAPERS = {"Next"}
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".jxl")
# Accent colours (a Windows 11 like palette, VeltOS blue first).
ACCENTS = ["#2F5EE6", "#0078D4", "#0099BC", "#00B294", "#10893E", "#498205",
           "#C239B3", "#8764B8", "#E3008C", "#E74856", "#F7630C", "#CA5010",
           "#FFB900", "#7A7574", "#567C73", "#4C4A48"]

# Themes (Personalization > Themes), like Windows 11's: a wallpaper (package
# id in WALLPAPER_DIRS, from veltos-desktop), light or dark mode and an
# accent colour with its name. The first two are the defaults.
THEMES = [
    {"id": "veltos-light", "title": ("VeltOS (light)", "VeltOS (açık)"), "wallpaper": "VeltOS",
     "dark": False, "accent": "#2F5EE6", "colour": ("Blue", "Mavi")},
    {"id": "veltos-dark", "title": ("VeltOS (dark)", "VeltOS (koyu)"), "wallpaper": "VeltOS",
     "dark": True, "accent": "#2F5EE6", "colour": ("Blue", "Mavi")},
    {"id": "lake", "title": ("Lake", "Göl"), "wallpaper": "VeltOS-Lake",
     "dark": False, "accent": "#0F7AC8", "colour": ("Sky blue", "Gök mavisi")},
    {"id": "nebula", "title": ("Nebula", "Bulutsu"), "wallpaper": "VeltOS-Nebula",
     "dark": True, "accent": "#8E5BE8", "colour": ("Purple", "Mor")},
    {"id": "ember", "title": ("Ember", "Kor"), "wallpaper": "VeltOS-Ember",
     "dark": True, "accent": "#D6243B", "colour": ("Red", "Kırmızı")},
    {"id": "tide", "title": ("Tide", "Gelgit"), "wallpaper": "VeltOS-Tide",
     "dark": False, "accent": "#12949B", "colour": ("Teal", "Turkuaz")},
    {"id": "dawn", "title": ("Dawn", "Şafak"), "wallpaper": "VeltOS-Dawn",
     "dark": False, "accent": "#5A6B85", "colour": ("Slate", "Arduvaz")},
    {"id": "flow", "title": ("Flow", "Akış"), "wallpaper": "VeltOS-Flow",
     "dark": False, "accent": "#5B3FE0", "colour": ("Indigo", "Çivit")},
]
# The colour scheme's own accent (no AccentColor in kdeglobals).
DEFAULT_ACCENT = "#2F5EE6"


def wallpaper_id(path):
    """The wallpaper package id of a path or id ("" for none)."""
    return Path(str(path).rstrip("/")).name if path else ""


def current_theme(wallpaper, dark, accent):
    """The id of the theme the desktop matches, "" for a custom mix. An
    unset wallpaper is VeltOS' default, an unset accent the scheme's."""
    wallpaper = wallpaper_id(wallpaper) or "VeltOS"
    accent = (accent or DEFAULT_ACCENT).upper()
    for theme in THEMES:
        if theme["wallpaper"] == wallpaper and theme["dark"] == dark and theme["accent"].upper() == accent:
            return theme["id"]
    return ""


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def package_title(package):
    """A wallpaper package's display name (metadata.json), else its id."""
    try:
        meta = json.loads((package / "metadata.json").read_text(encoding="utf-8"))
        return meta["KPlugin"]["Name"] or package.name
    except (OSError, ValueError, KeyError, TypeError):
        return package.name


class Personalization:
    def __init__(self, runner=run):
        self.run = runner

    def wallpapers(self):
        """Installed wallpaper packages: name, preview image and path."""
        result = []
        for base in WALLPAPER_DIRS:
            if not base.is_dir():
                continue
            for package in sorted(base.iterdir()):
                if package.name in HIDDEN_WALLPAPERS:
                    continue
                images = package / "contents" / "images"
                if not images.is_dir():
                    continue
                preview = package / "contents" / "screenshot.png"
                if not preview.exists():
                    candidates = sorted(p for p in images.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
                    if not candidates:
                        continue
                    # The largest picture is the sharpest preview.
                    preview = max(candidates, key=lambda p: p.stat().st_size)
                dark = package / "contents" / "screenshot-dark.png"
                result.append({"name": package.name, "title": package_title(package),
                               "preview": str(preview), "previewDark": str(dark if dark.exists() else preview),
                               "path": str(package)})
        result.sort(key=lambda w: (w["name"] != "VeltOS", w["name"].lower()))
        return result

    def current_wallpaper(self):
        """The desktop picture Plasma shows ("" if it is the default)."""
        try:
            text = (config_home() / "plasma-org.kde.plasma.desktop-appletsrc").read_text(
                encoding="utf-8", errors="replace")
        except OSError:
            return ""
        match = re.search(r"^Image=(.+)$", text, re.M)
        if not match:
            return ""
        value = match.group(1).strip()
        value = re.sub(r"^file://", "", value)
        return value.rstrip("/")

    def set_wallpaper(self, path):
        return self.run(["plasma-apply-wallpaperimage", str(path)])[0] == 0

    def accent(self):
        """The chosen accent colour as #RRGGBB ("" for the theme's own)."""
        try:
            text = (config_home() / "kdeglobals").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        general = re.search(r"^\[General\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
        match = re.search(r"^AccentColor=(\d+),(\d+),(\d+)", general.group(1), re.M) if general else None
        if not match:
            match = re.search(r"^AccentColor=#?([0-9A-Fa-f]{6})\s*$", general.group(1), re.M) if general else None
            return "#" + match.group(1).upper() if match else ""
        return "#{:02X}{:02X}{:02X}".format(*(int(v) for v in match.groups()))

    def set_accent(self, color):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            return False
        if self.run(["plasma-apply-colorscheme", "--accent-color", color])[0] != 0:
            return False
        # plasma-apply-colorscheme writes the colours but not the choice
        # (Plasma 6.3, VM 2026-10-21); KDE's colours module records it as
        # AccentColor, which accent() reads and the global theme keeps when
        # light and dark mode are switched.
        rgb = ",".join(str(int(color[i:i + 2], 16)) for i in (1, 3, 5))
        self.run(["kwriteconfig6", "--file", "kdeglobals", "--group", "General", "--key", "AccentColor", rgb])
        # Tell running programs the palette changed (KGlobalSettings
        # PaletteChanged, as KDE's colours module does): plasmashell (the
        # taskbar's accent glow, Start, the flyouts) kept the old accent
        # until it was restarted (VM, 2026-10-22).
        self.run(PALETTE_CHANGED)
        return True

    def set_mode(self, mode_command, accent=""):
        """Light or dark (the global theme), then the chosen accent colour
        again and the palette notice, so the running taskbar, Start and the
        flyouts take the new colours at once."""
        ok = self.run(mode_command, timeout=120)[0] == 0
        if accent:
            return self.set_accent(accent) and ok
        self.run(PALETTE_CHANGED)
        return ok

    def apply_theme(self, wallpaper, accent, mode_command=None):
        """Apply a theme in order: light/dark first (the global theme sets
        the colour scheme), then the wallpaper, then the accent colour on
        the new scheme."""
        ok = True
        if mode_command:
            ok = self.run(mode_command, timeout=120)[0] == 0
        ok = self.set_wallpaper(wallpaper) and ok
        return self.set_accent(accent) and ok

    def pick_image(self, start, title):
        """Ask for a picture with the VeltOS file dialog (File Explorer's
        Windows 11 style "Open"); "" if cancelled."""
        return pick_file(start, title, [{"name": PICTURES_FILTER[0], "patterns": PICTURES_FILTER[1]}])


PICTURES_FILTER = ("Pictures", ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.avif", "*.jxl", "*.bmp", "*.gif"])
# KGlobalSettings::notifyChange(PaletteChanged = 0, 0) on the session bus.
PALETTE_CHANGED = ["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
                   "org.kde.KGlobalSettings.notifyChange", "int32:0", "int32:0"]


def pick_file(start, title, filters, mode="open", run_dialog=None):
    """One file from `veltos-explorer --pick` (picker.py of File Explorer),
    which reads its request as JSON and answers with JSON; "" if cancelled."""
    request = {"mode": mode, "title": title, "current_folder": str(start), "filters": filters}
    run_dialog = run_dialog or (lambda command, text: subprocess.run(
        command, input=text, capture_output=True, text=True, timeout=3600).stdout)
    try:
        out = run_dialog(["veltos-explorer", "--pick"], json.dumps(request))
        answer = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return ""
    paths = answer.get("paths") if isinstance(answer, dict) else None
    return paths[0] if paths and isinstance(paths[0], str) else ""


# --- Time ------------------------------------------------------------------------------------------

def utc_offset(zone, now=None):
    """Minutes east of UTC for a time zone now (None if unknown)."""
    if ZoneInfo is None:
        return None
    try:
        moment = (now or datetime.datetime.now(datetime.timezone.utc)).astimezone(ZoneInfo(zone))
    except Exception:  # unknown or broken zone data
        return None
    offset = moment.utcoffset()
    return int(offset.total_seconds() // 60) if offset is not None else None


def zone_label(zone, offset):
    """"(UTC+03:00) Istanbul" style label, as Windows shows time zones."""
    place = zone.split("/")[-1].replace("_", " ")
    region = zone.split("/")[0] if "/" in zone else ""
    if region and region not in ("Etc",):
        place = f"{place} ({region.replace('_', ' ')})"
    if offset is None:
        return place
    sign = "+" if offset >= 0 else "-"
    hours, minutes = divmod(abs(offset), 60)
    return f"(UTC{sign}{hours:02d}:{minutes:02d}) {place}"


class Time:
    def __init__(self, runner=run):
        self.run = runner

    def status(self):
        code, out = self.run(["timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "CanNTP"])
        values = dict(line.split("=", 1) for line in out.splitlines() if "=" in line) if code == 0 else {}
        return {"timezone": values.get("Timezone", ""), "automatic": values.get("NTP") == "yes",
                "canAutomatic": values.get("CanNTP", "yes") == "yes"}

    def timezones(self, now=None):
        code, out = self.run(["timedatectl", "list-timezones"])
        zones = [line.strip() for line in out.splitlines() if line.strip()] if code == 0 else []
        result = []
        for zone in zones:
            offset = utc_offset(zone, now)
            result.append({"value": zone, "label": zone_label(zone, offset),
                           "offset": offset if offset is not None else 0})
        result.sort(key=lambda z: (z["offset"], z["label"]))
        return result

    def state(self):
        return dict(self.status(), zones=self.timezones())

    def set_timezone(self, zone, known=None):
        known = known if known is not None else [z["value"] for z in self.timezones()]
        if zone not in known:
            return False
        return self.run(["timedatectl", "set-timezone", zone], timeout=300)[0] == 0

    def set_automatic(self, on):
        return self.run(["timedatectl", "set-ntp", "true" if on else "false"], timeout=300)[0] == 0
