"""Settings kept in KDE configuration files, for the built-in pages that
replace KDE's settings modules (lock screen, night light, multitasking,
notifications, power, file search, text size, language and region,
keyboard layouts).

Values are read the way KDE reads them (the user's file over the system
file in /etc/xdg) and written with `kwriteconfig6`; after a change the
program that uses the value is asked to reload it (KWin, PowerDevil,
the keyboard layout service). Commands go through `run` so tests can use
a fake runner. Nothing here needs the administrator password.
"""

import configparser
import os
import re
from pathlib import Path

from .apps import desktop_info
from .devices import run


def config_dirs():
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    system = [Path(p) for p in (os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":") if p]
    return home, system


def group_name(groups):
    """configparser's name for the KDE group path ["AC", "Display"] ("AC][Display")."""
    return "][".join(groups)


def read_value(filename, groups, key, default=None, dirs=None):
    """A KConfig value as KDE sees it: the user's file wins over /etc/xdg."""
    home, system = dirs or config_dirs()
    for folder in [home, *system]:
        parser = configparser.RawConfigParser(interpolation=None, strict=False, delimiters=("=",))
        parser.optionxform = str
        try:
            parser.read(folder / filename, encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            continue
        section = group_name(groups)
        if parser.has_section(section) and parser.has_option(section, key):
            return parser.get(section, key)
    return default


def as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def as_int(value, default=0):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def write_command(filename, groups, key, value):
    # --notify: running programs that watch the file (KConfigWatcher:
    # Plasma's notifications, KDE apps' fonts and animations) update at once.
    command = ["kwriteconfig6", "--notify", "--file", filename]
    for group in groups:
        command += ["--group", group]
    if isinstance(value, bool):
        command += ["--type", "bool", "--key", key, "true" if value else "false"]
    else:
        command += ["--key", key, str(value)]
    return command


# --- what each setting is --------------------------------------------------------------------
# key: (file, group path, KConfig key, kind, default). Kinds: bool, int, str.
SETTINGS = {
    # Personalization > Lock screen; Privacy & security > Screen lock
    "autoLock": ("kscreenlockerrc", ["Daemon"], "Autolock", "bool", True),
    "lockAfter": ("kscreenlockerrc", ["Daemon"], "Timeout", "int", 5),          # minutes
    "lockOnResume": ("kscreenlockerrc", ["Daemon"], "LockOnResume", "bool", True),
    # System > Display > Night light
    "nightLight": ("kwinrc", ["NightColor"], "Active", "bool", False),
    "nightMode": ("kwinrc", ["NightColor"], "Mode", "str", "Automatic"),         # Automatic, Constant
    "nightTemperature": ("kwinrc", ["NightColor"], "NightTemperature", "int", 4500),
    # System > Multitasking
    "snapWindows": ("kwinrc", ["Windows"], "ElectricBorderTiling", "bool", True),
    "snapMaximize": ("kwinrc", ["Windows"], "ElectricBorderMaximize", "bool", True),
    # System > Notifications (plasma-workspace 6.3.6 notificationmanager kcfg files)
    "notificationSoundsMuted": ("plasmanotifyrc", ["DoNotDisturb"], "NotificationSoundsMuted", "bool", False),
    "criticalInDnd": ("plasmanotifyrc", ["Notifications"], "CriticalInDndMode", "bool", True),
    # System > Power (seconds; 0 = never)
    "screenOffAC": ("powerdevilrc", ["AC", "Display"], "TurnOffDisplayIdleTimeoutSec", "int", 600),
    "sleepAC": ("powerdevilrc", ["AC", "SuspendAndShutdown"], "AutoSuspendIdleTimeoutSec", "int", 900),
    "screenOffBattery": ("powerdevilrc", ["Battery", "Display"], "TurnOffDisplayIdleTimeoutSec", "int", 300),
    "sleepBattery": ("powerdevilrc", ["Battery", "SuspendAndShutdown"], "AutoSuspendIdleTimeoutSec", "int", 600),
    "powerButton": ("powerdevilrc", ["AC", "SuspendAndShutdown"], "PowerButtonAction", "int", 8),
    "lidAction": ("powerdevilrc", ["AC", "SuspendAndShutdown"], "LidAction", "int", 1),
}

# PowerDevil actions (powerdevil's PowerButtonAction / LidAction values).
POWER_ACTIONS = {"nothing": 0, "sleep": 1, "hibernate": 2, "shutdown": 8, "ask": 16, "screenoff": 64}
# Choices offered for "turn off my screen" / "put my device to sleep", in
# minutes as Windows offers them (0 = never).
TIMEOUT_MINUTES = [1, 2, 3, 5, 10, 15, 20, 25, 30, 45, 60, 120, 180, 240, 300, 0]
LOCK_MINUTES = [1, 2, 3, 5, 10, 15, 30, 60, 0]     # 0 = never (Autolock off)
NIGHT_TEMPERATURES = (6500, 1000)       # KWin's range: no change .. strongest

# What has to happen after a change (programs reload their settings).
RELOAD = {
    "kwinrc": [["qdbus6", "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"]],
    "powerdevilrc": [["qdbus6", "org.kde.Solid.PowerManagement", "/org/kde/Solid/PowerManagement",
                      "org.kde.Solid.PowerManagement.reparseConfiguration"]],
    "kxkbrc": [["dbus-send", "--session", "--type=signal", "/Layouts", "org.kde.keyboard.reloadConfig"]],
}


class Preferences:
    """Values of SETTINGS, changing them, and a few settings that are more
    than one key (do not disturb, power button on battery, file search,
    text size, language, keyboard layouts)."""

    def __init__(self, runner=run, dirs=None):
        self.run = runner
        self.dirs = dirs

    def get(self, name):
        filename, groups, key, kind, default = SETTINGS[name]
        value = read_value(filename, groups, key, None, self.dirs)
        if kind == "bool":
            return as_bool(value, default)
        if kind == "int":
            return as_int(value, default)
        return default if value is None else value

    def set(self, name, value):
        filename, groups, key, kind, _default = SETTINGS[name]
        if kind == "bool":
            value = bool(value)
        elif kind == "int":
            value = as_int(value)
        else:
            value = str(value)
        if name == "lockAfter":
            # "Never" is Windows' last choice in the list: the lock screen's
            # automatic lock goes off (a timeout of 0 would not mean that).
            ok = self.run(write_command(filename, groups, "Autolock", value > 0))[0] == 0
            if value <= 0:
                return ok
        ok = self.run(write_command(filename, groups, key, value))[0] == 0
        if name == "powerButton" or name == "lidAction":
            # One choice for every power state, as Windows asks it once.
            for state in ("Battery", "LowBattery"):
                self.run(write_command(filename, [state, groups[1]], key, value))
        if name == "nightLight" and value:
            # Windows' night light without a schedule is on all the time.
            self.run(write_command("kwinrc", ["NightColor"], "Mode", "Constant"))
        for command in RELOAD.get(filename, []):
            self.run(command)
        return ok

    # --- several keys at once ------------------------------------------------------------------

    def animations(self):
        value = read_value("kdeglobals", ["KDE"], "AnimationDurationFactor", "1", self.dirs)
        try:
            return float(value) > 0
        except (TypeError, ValueError):
            return True

    def set_animations(self, on):
        return self.run(write_command("kdeglobals", ["KDE"], "AnimationDurationFactor", "1" if on else "0"))[0] == 0

    def do_not_disturb(self):
        """Plasma keeps "do not disturb" as an end time (KConfig date:
        "year,month,day,hour,minute,second"); a date far ahead means "until
        turned off"."""
        until = read_value("plasmanotifyrc", ["DoNotDisturb"], "Until", "", self.dirs) or ""
        return until[:4].isdigit() and until[:4] >= "2100"

    def set_do_not_disturb(self, on):
        value = "2999,12,31,0,0,0" if on else ""
        return self.run(write_command("plasmanotifyrc", ["DoNotDisturb"], "Until", value))[0] == 0

    def notification_apps(self, app_dirs=None, lang="en"):
        """Apps that have sent notifications (Plasma lists them under
        [Applications]) with their name, icon and whether banners show."""
        home, system = self.dirs or config_dirs()
        parser = configparser.RawConfigParser(interpolation=None, strict=False, delimiters=("=",))
        parser.optionxform = str
        try:
            parser.read(home / "plasmanotifyrc", encoding="utf-8")
        except (configparser.Error, OSError, UnicodeDecodeError):
            return []
        result = []
        for section in parser.sections():
            if not section.startswith("Applications]["):
                continue
            entry = section.split("][", 1)[1]
            info = desktop_info(entry, app_dirs, lang)
            if info is None:
                continue
            result.append(dict(info, id=entry,
                               banners=as_bool(parser.get(section, "ShowPopups", fallback="true"), True)))
        return sorted(result, key=lambda a: a["name"].lower())

    def set_app_banners(self, entry, on):
        if not re.fullmatch(r"[A-Za-z0-9._-]+", entry):
            return False
        return self.run(write_command("plasmanotifyrc", ["Applications", entry], "ShowPopups", bool(on)))[0] == 0

    def file_search(self):
        """Whether the file indexer is on: its setting (baloofilerc), as
        KDE's own page reads it. `balooctl6 status` said "not running" right
        after enabling, so the switch fell back to off (2026-10-21)."""
        return as_bool(read_value("baloofilerc", ["Basic Settings"], "Indexing-Enabled", None, self.dirs), True)

    def set_file_search(self, on):
        # balooctl6 writes the setting and starts or stops the indexer.
        ok = self.run(["balooctl6", "enable" if on else "disable"], timeout=60)[0] == 0
        if not ok:
            # Without baloo's tools the setting is still recorded for them.
            ok = self.run(write_command("baloofilerc", ["Basic Settings"], "Indexing-Enabled", bool(on)))[0] == 0
        return ok

    # Text size: the scale of the KDE fonts (Accessibility > Text size).
    BASE_FONTS = {"font": 10, "menuFont": 10, "toolBarFont": 10, "smallestReadableFont": 8}

    def text_size(self):
        value = read_value("kdeglobals", ["General"], "font", "", self.dirs) or ""
        parts = value.split(",")
        if len(parts) > 1 and parts[1].replace(".", "", 1).isdigit():
            return int(round(100 * float(parts[1]) / self.BASE_FONTS["font"]))
        return 100

    def set_text_size(self, percent):
        """Scale the KDE fonts (Plasma, KDE and Qt programs; GTK programs
        follow through KDE's GTK settings service). VeltOS' own apps read
        the same value (veltos_common.textscale) and scale their text."""
        percent = max(100, min(225, int(percent)))
        ok = True
        for key, base in self.BASE_FONTS.items():
            current = read_value("kdeglobals", ["General"], key, "", self.dirs) or ""
            family = current.split(",")[0] or "Inter"
            size = round(base * percent / 100, 1)
            ok &= self.run(write_command("kdeglobals", ["General"], key,
                                         f"{family},{size:g},-1,5,400,0,0,0,0,0,0,0,0,0,0,1"))[0] == 0
        # Running KDE and Qt programs re-read their fonts on this signal
        # (KGlobalSettings::FontChanged = 1), as KDE's Fonts page sends it.
        self.run(["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
                  "org.kde.KGlobalSettings.notifyChange", "int32:1", "int32:0"])
        return ok

    # Language and formats (Time & language > Language & region): Plasma
    # starts the session with them, so they apply after signing in again.
    def language(self):
        value = read_value("plasma-localerc", ["Translations"], "LANGUAGE", "", self.dirs) or ""
        first = value.split(":")[0] or os.environ.get("LANG", "en_US").split(".")[0]
        return "tr" if first.startswith("tr") else "en"

    def set_language(self, code):
        languages = {"en": "en_US", "tr": "tr"}
        if code not in languages:
            return False
        return self.run(write_command("plasma-localerc", ["Translations"], "LANGUAGE", languages[code]))[0] == 0

    def formats(self):
        value = read_value("plasma-localerc", ["Formats"], "LANG", "", self.dirs) or os.environ.get("LANG", "")
        return value.split(".")[0] if value else "en_US"

    def set_formats(self, locale_name, available):
        if locale_name not in available:
            return False
        return self.run(write_command("plasma-localerc", ["Formats"], "LANG", f"{locale_name}.UTF-8"))[0] == 0

    def available_formats(self):
        """Locales the system can format with (`locale -a`, UTF-8 ones)."""
        code, out = self.run(["locale", "-a"])
        names = set()
        for line in out.splitlines() if code == 0 else []:
            match = re.fullmatch(r"([a-z]{2,3}_[A-Z]{2})\.(utf8|UTF-8)", line.strip())
            if match:
                names.add(match.group(1))
        names.update(["en_US", "tr_TR"])
        return sorted(names)

    # Keyboard layouts (Time & language > Typing).
    def layouts(self):
        value = read_value("kxkbrc", ["Layout"], "LayoutList", "", self.dirs) or ""
        layouts = [v for v in value.split(",") if v]
        return layouts or ["us"]

    def set_layouts(self, layouts):
        layouts = [l for l in layouts if re.fullmatch(r"[a-z]{2,3}(\([a-z0-9_]+\))?", l)]
        if not layouts:
            return False
        ok = self.run(write_command("kxkbrc", ["Layout"], "LayoutList", ",".join(layouts)))[0] == 0
        ok &= self.run(write_command("kxkbrc", ["Layout"], "Use", True))[0] == 0
        for command in RELOAD["kxkbrc"]:
            self.run(command)
        return ok

    def state(self):
        values = {name: self.get(name) for name in SETTINGS}
        if not values["autoLock"]:
            values["lockAfter"] = 0             # shown as "Never"
        values.update({
            "animations": self.animations(),
            "doNotDisturb": self.do_not_disturb(),
            "fileSearch": self.file_search(),
            "textSize": self.text_size(),
            "language": self.language(),
            "formats": self.formats(),
            "layouts": self.layouts(),
            "hasBattery": has_battery(),
        })
        return values


def has_battery(root="/sys/class/power_supply"):
    """A laptop battery (not a mouse's or a UPS's)."""
    base = Path(root)
    if not base.is_dir():
        return False
    for supply in base.iterdir():
        try:
            kind = (supply / "type").read_text().strip()
            scope = (supply / "scope").read_text().strip() if (supply / "scope").exists() else "System"
        except OSError:
            continue
        if kind == "Battery" and scope == "System":
            return True
    return False


# Keyboard layouts offered in Typing (xkb names; English and Turkish names).
# The layouts offered under "Add a keyboard": the common ones, Turkish first
# (product owner, 2026-10-22). Names checked against xkeyboard-config's
# rules/evdev.lst in the live image (layout, or layout(variant)).
KEYBOARD_LAYOUTS = [
    ("tr", "Turkish Q", "Türkçe Q"),
    ("tr(f)", "Turkish F", "Türkçe F"),
    ("tr(alt)", "Turkish Alt-Q", "Türkçe Alt-Q"),
    ("us", "English (US)", "İngilizce (ABD)"),
    ("gb", "English (UK)", "İngilizce (BK)"),
    ("de", "German", "Almanca"),
    ("at", "German (Austria)", "Almanca (Avusturya)"),
    ("ch", "German (Switzerland)", "Almanca (İsviçre)"),
    ("fr", "French", "Fransızca"),
    ("ca", "French (Canada)", "Fransızca (Kanada)"),
    ("be", "Belgian", "Belçika"),
    ("es", "Spanish", "İspanyolca"),
    ("latam", "Spanish (Latin American)", "İspanyolca (Latin Amerika)"),
    ("it", "Italian", "İtalyanca"),
    ("pt", "Portuguese", "Portekizce"),
    ("br", "Portuguese (Brazil)", "Portekizce (Brezilya)"),
    ("nl", "Dutch", "Felemenkçe"),
    ("ru", "Russian", "Rusça"),
    ("ua", "Ukrainian", "Ukraynaca"),
    ("pl", "Polish", "Lehçe"),
    ("cz", "Czech", "Çekçe"),
    ("sk", "Slovak", "Slovakça"),
    ("hu", "Hungarian", "Macarca"),
    ("ro", "Romanian", "Rumence"),
    ("bg", "Bulgarian", "Bulgarca"),
    ("gr", "Greek", "Yunanca"),
    ("hr", "Croatian", "Hırvatça"),
    ("rs", "Serbian", "Sırpça"),
    ("si", "Slovenian", "Slovence"),
    ("mk", "Macedonian", "Makedonca"),
    ("lt", "Lithuanian", "Litvanca"),
    ("lv", "Latvian", "Letonca"),
    ("ee", "Estonian", "Estonca"),
    ("fi", "Finnish", "Fince"),
    ("se", "Swedish", "İsveççe"),
    ("no", "Norwegian", "Norveççe"),
    ("dk", "Danish", "Danca"),
    ("is", "Icelandic", "İzlandaca"),
    ("ie", "Irish", "İrlandaca"),
    ("ara", "Arabic", "Arapça"),
    ("il", "Hebrew", "İbranice"),
    ("ir", "Persian", "Farsça"),
    ("az", "Azerbaijani", "Azerbaycanca"),
    ("kz", "Kazakh", "Kazakça"),
    ("ge", "Georgian", "Gürcüce"),
    ("in", "Indian", "Hint"),
    ("jp", "Japanese", "Japonca"),
    ("kr", "Korean", "Korece"),
    ("cn", "Chinese", "Çince"),
    ("th", "Thai", "Tayca"),
    ("vn", "Vietnamese", "Vietnamca"),
]
