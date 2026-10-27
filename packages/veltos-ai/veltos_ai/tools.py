"""What VeltOS AI may do on the computer: a list of actions. Looking things
up (the PC's details, file names, Wi-Fi networks) runs at once; everything
that changes something, opens something or reads a file's contents waits
for the user's "Allow" in the panel, as Copilot asks on Windows 11. The
changes go through the same helpers as VeltOS Settings (light/dark,
volume, Wi-Fi, Bluetooth, night light, power mode, time zone), so they
behave the same.

Since 2026-10-27 the list covers the whole system at the user's direction
(product owner: "VeltOS AI should reach everything in the OS"): apps
(install, uninstall, through PackageKit), updates, files in the home
folder, power (lock, sleep, restart), and `run_command` for anything the
other actions do not cover. A command is shown in full in the panel and
runs only after "Allow"; with `administrator` it runs through pkexec, so
VeltOS' own password prompt (veltos-auth) asks for the administrator's
password before anything happens. Installs and updates ask the same way
(polkit). Nothing runs with administrator rights without that password.

`TOOLS` describes the actions to the AI service (JSON Schema); `validate`
checks what the service sent before anything runs (a streamed tool input
may be cut off or wrong); `execute` runs an action and returns a short
JSON text for the service.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import strings

SETTINGS_PAGES = ("home", "system", "display", "sound", "notifications", "power", "storage", "about",
                  "bluetooth", "devices", "mouse", "keyboard", "network", "wifi", "personalization", "background",
                  "colors", "themes", "lockscreen", "taskbar", "apps", "defaultapps", "startup", "windows-apps",
                  "accounts", "yourinfo", "signin", "time", "datetime", "region", "gaming", "accessibility",
                  "privacy", "update")
FOLDERS = ("home", "desktop", "documents", "downloads", "pictures", "music", "videos", "this_pc", "recycle_bin")
POWER_MODES = ("power-saver", "balanced", "performance")
POWER_ACTIONS = ("lock", "sleep", "sign_out", "restart", "shut_down")
COMMAND_TIMEOUT = 300
MAX_OUTPUT = 6000
MAX_READ = 20000
XDG_NAMES = {"desktop": "DESKTOP", "documents": "DOCUMENTS", "downloads": "DOWNLOAD", "pictures": "PICTURES",
             "music": "MUSIC", "videos": "VIDEOS"}


def obj(properties=None, required=()):
    return {"type": "object", "properties": properties or {}, "required": list(required)}


TOOLS = [
    {"name": "get_system_info", "description": "Details of this computer: operating system and version, "
     "processor, memory, disk space, battery, Wi-Fi and Bluetooth state, current volume. Read-only.",
     "parameters": obj()},
    {"name": "search_files", "description": "Find files and folders in the user's home folder whose name "
     "contains the text. Returns up to 20 paths. Read-only.",
     "parameters": obj({"query": {"type": "string", "description": "Part of a file or folder name"}}, ["query"])},
    {"name": "open_app", "description": "Open (start, launch) an installed app by its name as shown in Start, "
     "for example \"File Explorer\", \"Notepad\", \"Calculator\", \"Firefox\", \"Word\" (Turkish: "
     "\"... aç\", \"Hesap Makinesi\", \"Not Defteri\", \"Dosya Gezgini\").",
     "parameters": obj({"name": {"type": "string", "description": "The app's name"}}, ["name"])},
    {"name": "open_settings", "description": "Open a page of VeltOS Settings.",
     "parameters": obj({"page": {"type": "string", "enum": list(SETTINGS_PAGES)}}, ["page"])},
    {"name": "set_theme", "description": "Switch the whole system between light and dark mode (Turkish: "
     "\"koyu mod\", \"karanlık mod\", \"açık mod\", \"aydınlık mod\").",
     "parameters": obj({"mode": {"type": "string", "enum": ["light", "dark"]}}, ["mode"])},
    {"name": "set_volume", "description": "Set the speaker volume in percent (0-100); this also unmutes.",
     "parameters": obj({"percent": {"type": "integer", "description": "0 to 100"}}, ["percent"])},
    {"name": "set_mute", "description": "Mute or unmute the speakers.",
     "parameters": obj({"muted": {"type": "boolean"}}, ["muted"])},
    {"name": "set_wifi", "description": "Turn Wi-Fi on or off.",
     "parameters": obj({"on": {"type": "boolean"}}, ["on"])},
    {"name": "set_bluetooth", "description": "Turn Bluetooth on or off.",
     "parameters": obj({"on": {"type": "boolean"}}, ["on"])},
    {"name": "set_do_not_disturb", "description": "Turn Do not disturb (no notification pop-ups) on or off.",
     "parameters": obj({"on": {"type": "boolean"}}, ["on"])},
    {"name": "open_url", "description": "Open a web page (http or https) in the web browser.",
     "parameters": obj({"url": {"type": "string"}}, ["url"])},
    {"name": "open_folder", "description": "Open a folder in File Explorer: one of the known folders, or a "
     "path inside the user's home folder.",
     "parameters": obj({"folder": {"type": "string", "enum": list(FOLDERS)},
                        "path": {"type": "string", "description": "Optional path inside the home folder"}},
                       ["folder"])},
    {"name": "take_screenshot", "description": "Start Snipping Tool to take a screenshot (Turkish: \"ekran "
     "görüntüsü al\"); only when the user asks for a screenshot.", "parameters": obj()},
    {"name": "set_night_light", "description": "Turn night light (warmer screen colours) on or off.",
     "parameters": obj({"on": {"type": "boolean"}}, ["on"])},
    {"name": "set_power_mode", "description": "Choose the power mode: power-saver (best battery), balanced or "
     "performance.", "parameters": obj({"mode": {"type": "string", "enum": list(POWER_MODES)}}, ["mode"])},
    {"name": "set_brightness", "description": "Set the screen brightness in percent (1-100).",
     "parameters": obj({"percent": {"type": "integer", "description": "1 to 100"}}, ["percent"])},
    {"name": "set_airplane_mode", "description": "Turn airplane mode on (Wi-Fi and Bluetooth off) or off "
     "(both on again).", "parameters": obj({"on": {"type": "boolean"}}, ["on"])},
    {"name": "list_wifi_networks", "description": "The Wi-Fi networks in range with their signal strength and "
     "whether they need a password. Read-only.", "parameters": obj()},
    {"name": "connect_wifi", "description": "Connect to a Wi-Fi network by its name; give the password for a "
     "new secured network.",
     "parameters": obj({"name": {"type": "string"}, "password": {"type": "string"}}, ["name"])},
    {"name": "set_wallpaper", "description": "Set the desktop background to a picture file.",
     "parameters": obj({"path": {"type": "string", "description": "The picture's path"}}, ["path"])},
    {"name": "set_timezone", "description": "Set the time zone, for example Europe/Istanbul or America/New_York.",
     "parameters": obj({"zone": {"type": "string"}}, ["zone"])},
    {"name": "power", "description": "Lock the screen, sleep, sign out, restart or shut down the computer, only "
     "when the user asks exactly that (Turkish: \"kilitle\", \"uyku\", \"oturumu kapat\", \"yeniden başlat\", "
     "\"bilgisayarı kapat\").",
     "parameters": obj({"action": {"type": "string", "enum": list(POWER_ACTIONS)}}, ["action"])},
    {"name": "install_app", "description": "Install an app or program from Debian's archive (VeltOS Store) by its "
     "Debian package name, for example vlc, gimp, inkscape, kdenlive, obs-studio, steam-installer, thunderbird. "
     "VeltOS asks for the administrator's password.",
     "parameters": obj({"package": {"type": "string", "description": "Debian package name"}}, ["package"])},
    {"name": "uninstall_app", "description": "Uninstall an app by its Debian package name. Parts of VeltOS "
     "itself cannot be removed. VeltOS asks for the administrator's password.",
     "parameters": obj({"package": {"type": "string"}}, ["package"])},
    {"name": "install_updates", "description": "Download and install every available update of the system and "
     "its apps. VeltOS asks for the administrator's password.", "parameters": obj()},
    {"name": "create_folder", "description": "Create a folder inside the user's home folder.",
     "parameters": obj({"path": {"type": "string", "description": "Path inside the home folder"}}, ["path"])},
    {"name": "move_to_recycle_bin", "description": "Move a file or folder of the home folder to the Recycle Bin "
     "(it can be restored from there).", "parameters": obj({"path": {"type": "string"}}, ["path"])},
    {"name": "empty_recycle_bin", "description": "Empty the Recycle Bin (its files are deleted for good).",
     "parameters": obj()},
    {"name": "open_file", "description": "Open a file of the home folder with its default app.",
     "parameters": obj({"path": {"type": "string"}}, ["path"])},
    {"name": "read_text_file", "description": "Read a text file of the home folder (up to 20,000 characters) to "
     "answer questions about it.", "parameters": obj({"path": {"type": "string"}}, ["path"])},
    {"name": "write_text_file", "description": "Write a text file in the home folder (a note, a list, a script). "
     "An existing file is only replaced with overwrite set to true.",
     "parameters": obj({"path": {"type": "string"}, "text": {"type": "string"},
                        "overwrite": {"type": "boolean"}}, ["path", "text"])},
    {"name": "run_command", "description": "Run a shell command (bash) on this computer and get its output, "
     "only for a task on this computer that no other action does (for example \"uname -r\" for the Linux "
     "version). Never for general questions: answer those yourself. The user sees the exact command and must "
     "allow it. Set administrator to true only for commands that need root (apt, system files); VeltOS then "
     "asks for the administrator's password. Never for interactive programs.",
     "parameters": obj({"command": {"type": "string"}, "administrator": {"type": "boolean"}}, ["command"])},
]
BY_NAME = {tool["name"]: tool for tool in TOOLS}
READ_ONLY = ("get_system_info", "search_files", "list_wifi_networks")


def validate(name, arguments):
    """The arguments if they fit the action's schema, else None."""
    tool = BY_NAME.get(name)
    if tool is None or not isinstance(arguments, dict):
        return None
    schema = tool["parameters"]
    for key in schema["required"]:
        if key not in arguments:
            return None
    clean = {}
    for key, value in arguments.items():
        spec = schema["properties"].get(key)
        if spec is None:
            continue                       # unknown extras are left out
        kind = spec["type"]
        if kind == "string" and not isinstance(value, str):
            return None
        if kind == "boolean" and not isinstance(value, bool):
            return None
        if kind == "integer":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
                return None
            value = int(value)
        if "enum" in spec and value not in spec["enum"]:
            return None
        clean[key] = value
    return clean


def needs_approval(name):
    return name not in READ_ONLY


def title(name, arguments, lang):
    """The action as the panel asks about it ("Switch to dark mode")."""
    a = arguments or {}
    if name == "set_theme":
        return strings.text(lang, "act_set_theme_" + ("dark" if a.get("mode") == "dark" else "light"))
    if name == "set_mute":
        return strings.text(lang, "act_mute" if a.get("muted") else "act_unmute")
    if name in ("set_wifi", "set_bluetooth", "set_do_not_disturb"):
        key = {"set_wifi": "wifi", "set_bluetooth": "bluetooth", "set_do_not_disturb": "dnd"}[name]
        return strings.text(lang, f"act_{key}_{'on' if a.get('on') else 'off'}")
    if name == "set_volume":
        return strings.text(lang, "act_set_volume", percent=max(0, min(100, int(a.get("percent", 0)))))
    if name == "open_folder":
        pair = strings.FOLDERS.get(a.get("folder", "home"), strings.FOLDERS["home"])
        folder = a.get("path") or (pair[1] if lang == "tr" else pair[0])
        return strings.text(lang, "act_open_folder", folder=folder)
    if name == "take_screenshot":
        return strings.text(lang, "act_screenshot")
    if name == "get_system_info":
        return strings.text(lang, "act_get_system_info")
    if name == "search_files":
        return strings.text(lang, "act_search_files", query=a.get("query", ""))
    if name == "open_app":
        return strings.text(lang, "act_open_app", name=a.get("name", ""))
    if name == "open_settings":
        return strings.text(lang, "act_open_settings", page=a.get("page", ""))
    if name == "open_url":
        return strings.text(lang, "act_open_url", url=a.get("url", ""))
    if name in ("set_night_light", "set_airplane_mode"):
        key = {"set_night_light": "night", "set_airplane_mode": "airplane"}[name]
        return strings.text(lang, f"act_{key}_{'on' if a.get('on') else 'off'}")
    if name == "set_power_mode":
        return strings.text(lang, "act_power_mode_" + a.get("mode", "balanced").replace("-", "_"))
    if name == "set_brightness":
        return strings.text(lang, "act_set_brightness", percent=max(1, min(100, int(a.get("percent", 50)))))
    if name == "power":
        return strings.text(lang, "act_power_" + a.get("action", "lock"))
    if name == "run_command":
        key = "act_run_command_admin" if a.get("administrator") else "act_run_command"
        return strings.text(lang, key, command=a.get("command", ""))
    simple = {"list_wifi_networks": {}, "connect_wifi": {"name": a.get("name", "")},
              "set_wallpaper": {"path": a.get("path", "")}, "set_timezone": {"zone": a.get("zone", "")},
              "install_app": {"package": a.get("package", "")}, "uninstall_app": {"package": a.get("package", "")},
              "install_updates": {}, "create_folder": {"path": a.get("path", "")},
              "move_to_recycle_bin": {"path": a.get("path", "")}, "empty_recycle_bin": {},
              "open_file": {"path": a.get("path", "")}, "read_text_file": {"path": a.get("path", "")},
              "write_text_file": {"path": a.get("path", "")}}
    if name in simple:
        return strings.text(lang, "act_" + name, **simple[name])
    return name


# --- running them ---------------------------------------------------------------------------------

def run(command, timeout=30):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return result.returncode, result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def start(command):
    """A program that outlives the panel."""
    subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


def home():
    return Path(os.environ.get("HOME") or Path.home())


def user_dir(name):
    code, out = run(["xdg-user-dir", XDG_NAMES[name]], timeout=5)
    path = Path(out.strip()) if code == 0 and out.strip() else home() / name.capitalize()
    return path


def application_dirs():
    data_home = Path(os.environ.get("XDG_DATA_HOME") or home() / ".local/share")
    dirs = [data_home] + [Path(d) for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")]
    return [d / "applications" for d in dirs]


def loose(text):
    """Folded for matching names typed in Turkish or English: İ, I and ı all
    become i ("Inkscape" typed "inkscape", "İndir" as "indir")."""
    return text.replace("İ", "i").replace("I", "i").lower().replace("ı", "i").replace("\u0307", "").strip()


def find_app(name, lang="en", dirs=None):
    """(desktop file, shown name) of the app whose name fits best, or None."""
    wanted = loose(name)
    best = None
    for directory in dirs or application_dirs():
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.desktop"):
            fields = {}
            try:
                in_entry = False
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("["):
                        in_entry = line.strip() == "[Desktop Entry]"
                        continue
                    if in_entry and "=" in line:
                        key, _, value = line.partition("=")
                        fields.setdefault(key.strip(), value.strip())
            except OSError:
                continue
            if fields.get("NoDisplay") == "true" or fields.get("Hidden") == "true" or fields.get("Type") != "Application":
                continue
            names = [fields.get(f"Name[{lang}]", ""), fields.get("Name", ""), fields.get(f"GenericName[{lang}]", ""),
                     fields.get("GenericName", "")]
            shown = fields.get(f"Name[{lang}]") or fields.get("Name") or path.stem
            for rank, candidate in enumerate(names):
                folded = loose(candidate)
                if not folded:
                    continue
                score = 0 if folded == wanted else (10 if folded.startswith(wanted) else
                                                      (20 if wanted in folded else None))
                if score is None:
                    continue
                score += rank
                if best is None or score < best[0]:
                    best = (score, path, shown)
    return (best[1], best[2]) if best else None


def system_info():
    info = {"os": "", "kernel": platform.release(), "processor": "", "cores": os.cpu_count() or 0}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                info["os"] = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                info["processor"] = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    try:
        memory = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            memory[key] = int(value.split()[0]) if value.split() else 0
        info["memory_total_gb"] = round(memory.get("MemTotal", 0) / 1048576, 1)
        info["memory_available_gb"] = round(memory.get("MemAvailable", 0) / 1048576, 1)
    except (OSError, ValueError):
        pass
    try:
        usage = shutil.disk_usage(str(home()))
        info["disk_total_gb"] = round(usage.total / 1e9, 1)
        info["disk_free_gb"] = round(usage.free / 1e9, 1)
    except OSError:
        pass
    batteries = sorted(Path("/sys/class/power_supply").glob("BAT*")) if Path("/sys/class/power_supply").is_dir() else []
    if batteries:
        try:
            info["battery_percent"] = int((batteries[0] / "capacity").read_text().strip())
            info["battery_status"] = (batteries[0] / "status").read_text().strip()
        except (OSError, ValueError):
            pass
    code, out = run(["nmcli", "-t", "-f", "WIFI", "radio"], timeout=5)
    if code == 0:
        info["wifi"] = out.strip()
    code, out = run(["bluetoothctl", "show"], timeout=5)
    if code == 0:
        info["bluetooth"] = "enabled" if re.search(r"Powered:\s*yes", out) else "disabled"
    code, out = run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], timeout=5)
    match = re.search(r"(\d+)%", out) if code == 0 else None
    if match:
        info["volume_percent"] = int(match.group(1))
    return info


def search_files(query, limit=20, root=None):
    """Paths under the home folder whose name contains the query (hidden folders skipped)."""
    query = query.casefold().strip()
    if not query:
        return []
    root = Path(root or home())
    found = []
    for directory, folders, files in os.walk(root):
        folders[:] = [f for f in folders if not f.startswith(".")]
        for name in folders + files:
            if query in name.casefold():
                found.append(str(Path(directory) / name))
                if len(found) >= limit:
                    return found
    return found


def settings_helpers():
    """VeltOS Settings' own helpers (theme, sound, Wi-Fi, Bluetooth)."""
    from veltos_settings import devices
    return devices


def set_theme(dark):
    devices = settings_helpers()
    from veltos_settings.app import APPLY_THEME, DESKTOP_THEME, LOOK_AND_FEEL
    personal = devices.Personalization()
    command = ["sh", "-c", APPLY_THEME, "sh", LOOK_AND_FEEL[dark], DESKTOP_THEME[dark], "dark" if dark else "light"]
    return personal.set_mode(command, personal.accent())


def home_path(value, must_exist=True):
    """A path inside the home folder (relative ones are taken from it), or
    None when it is outside or (with must_exist) missing."""
    path = Path(os.path.expanduser(str(value or "").strip()))
    path = path if path.is_absolute() else home() / path
    try:
        path = path.resolve()
        path.relative_to(home().resolve())
    except (OSError, ValueError):
        return None
    if must_exist and not path.exists():
        return None
    return path


def pkcon(arguments, runner=run):
    """(ok, error) of a PackageKit command. It runs in VeltOS Store's pseudo
    terminal (ptyrun: an interactive transaction, so polkit asks for the
    administrator's password through VeltOS' prompt)."""
    code, out = runner([sys.executable, "-m", "veltos_store.ptyrun", "pkcon", "-p", *arguments], timeout=3600)
    error = next((line.partition(":")[2].strip() for line in out.splitlines() if line.startswith("Fatal error:")), "")
    # pkcon exits 5 when there was nothing to do (already installed, no updates).
    return code in (0, 5) and not error, error


def lists_old():
    try:
        from veltos_store.packages import lists_need_refresh
    except ImportError:
        return False
    return lists_need_refresh()


def package_name(value):
    value = str(value or "").strip().lower()
    return value if re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", value) else ""


def set_brightness(percent, runner=run):
    """Plasma's screen brightness (PowerDevil's org.kde.ScreenBrightness, the
    older BrightnessControl action as a fallback)."""
    target = ["org.kde.ScreenBrightness", "/org/kde/ScreenBrightness/display0", "org.kde.ScreenBrightness.Display"]
    code, out = runner(["busctl", "--user", "get-property", *target, "MaxBrightness"], timeout=10)
    match = re.search(r"(\d+)\s*$", out.strip()) if code == 0 else None
    if match:
        value = max(1, round(int(match.group(1)) * percent / 100))
        if runner(["busctl", "--user", "call", *target, "SetBrightness", "iu", str(value), "0"], timeout=10)[0] == 0:
            return True
    actions = ["org.kde.Solid.PowerManagement", "/org/kde/Solid/PowerManagement/Actions/BrightnessControl",
               "org.kde.Solid.PowerManagement.Actions.BrightnessControl"]
    code, out = runner(["qdbus6", *actions[:2], actions[2] + ".brightnessMax"], timeout=10)
    if code != 0 or not out.strip().isdigit():
        return False
    value = max(1, round(int(out.strip()) * percent / 100))
    return runner(["qdbus6", *actions[:2], actions[2] + ".setBrightness", str(value)], timeout=10)[0] == 0


POWER_COMMANDS = {
    "lock": ["loginctl", "lock-session"],
    "sleep": ["systemctl", "suspend"],
    "sign_out": ["qdbus6", "org.kde.Shutdown", "/Shutdown", "org.kde.Shutdown.logout"],
    "restart": ["qdbus6", "org.kde.Shutdown", "/Shutdown", "org.kde.Shutdown.logoutAndReboot"],
    "shut_down": ["qdbus6", "org.kde.Shutdown", "/Shutdown", "org.kde.Shutdown.logoutAndShutdown"],
}


def run_command(command, administrator=False):
    """(exit code, output) of a command the user allowed; with administrator,
    through pkexec (VeltOS' password prompt)."""
    argv = ["bash", "-c", command]
    if administrator:
        argv = ["pkexec", *argv]
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=COMMAND_TIMEOUT, cwd=str(home()))
    except subprocess.TimeoutExpired as error:
        output = (error.output or b"").decode("utf-8", "replace")
        return 124, output[-MAX_OUTPUT:] + "\n(stopped after 5 minutes)"
    except OSError as error:
        return 127, str(error)
    return result.returncode, result.stdout.decode("utf-8", "replace")[-MAX_OUTPUT:]


def execute(name, arguments, lang="en", starter=start, runner=run, command_runner=run_command):
    """(ok, JSON text for the service)."""
    def answer(ok, **values):
        return ok, json.dumps({"ok": ok, **values}, ensure_ascii=False)

    a = arguments
    if name == "get_system_info":
        return answer(True, **system_info())
    if name == "search_files":
        return answer(True, paths=search_files(a["query"]))
    if name == "open_app":
        found = find_app(a["name"], lang)
        if not found:
            return answer(False, error=f"No installed app is called {a['name']!r}.")
        starter(["kioclient", "exec", str(found[0])])
        return answer(True, opened=found[1])
    if name == "open_settings":
        starter(["veltos-settings", a["page"]])
        return answer(True)
    if name == "set_theme":
        return answer(bool(set_theme(a["mode"] == "dark")), mode=a["mode"])
    if name == "set_volume":
        sound = settings_helpers().Sound(runner)
        ok = sound.set_muted("sink", False) and sound.set_volume("sink", a["percent"])
        return answer(ok, percent=max(0, min(100, a["percent"])))
    if name == "set_mute":
        return answer(settings_helpers().Sound(runner).set_muted("sink", a["muted"]), muted=a["muted"])
    if name == "set_wifi":
        return answer(settings_helpers().Network(runner).set_wifi(a["on"]), on=a["on"])
    if name == "set_bluetooth":
        return answer(settings_helpers().Bluetooth(runner).set_powered(a["on"]), on=a["on"])
    if name == "set_do_not_disturb":
        value = "2999,12,31,0,0,0" if a["on"] else ""
        code, _ = runner(["kwriteconfig6", "--notify", "--file", "plasmanotifyrc", "--group", "DoNotDisturb",
                          "--key", "Until", value])
        return answer(code == 0, on=a["on"])
    if name == "open_url":
        url = a["url"].strip()
        if not re.match(r"^https?://[^\s]+$", url, re.IGNORECASE):
            return answer(False, error="Only http and https addresses can be opened.")
        starter(["xdg-open", url])
        return answer(True)
    if name == "open_folder":
        folder = a["folder"]
        if a.get("path"):
            path = Path(os.path.expanduser(a["path"]))
            path = path if path.is_absolute() else home() / path
            try:
                path = path.resolve()
                path.relative_to(home().resolve())
            except (OSError, ValueError):
                return answer(False, error="Only folders inside the home folder can be opened.")
            if not path.is_dir():
                return answer(False, error="The folder does not exist.")
            target = str(path)
        elif folder == "this_pc":
            target = "thispc:"
        elif folder == "recycle_bin":
            target = "trash:/"
        elif folder == "home":
            target = str(home())
        else:
            target = str(user_dir(folder))
        starter(["veltos-explorer", target])
        return answer(True, folder=target)
    if name == "take_screenshot":
        starter(["veltos-snip", "--snip"])
        return answer(True)
    if name == "set_night_light":
        from veltos_settings.prefs import Preferences
        return answer(bool(Preferences(runner).set("nightLight", a["on"])), on=a["on"])
    if name == "set_power_mode":
        from veltos_settings.prefs import Preferences
        prefs = Preferences(runner)
        source = prefs.power_mode_state().get("powerSource", "ac")
        return answer(bool(prefs.set_power_mode(source, a["mode"])), mode=a["mode"])
    if name == "set_brightness":
        percent = max(1, min(100, a["percent"]))
        return answer(set_brightness(percent, runner), percent=percent)
    if name == "set_airplane_mode":
        devices = settings_helpers()
        wifi = devices.Network(runner).set_wifi(not a["on"])
        bluetooth = devices.Bluetooth(runner).set_powered(not a["on"])
        return answer(bool(wifi), on=a["on"], bluetooth_changed=bool(bluetooth))
    if name == "list_wifi_networks":
        networks = settings_helpers().Network(runner).networks(rescan=True)
        return answer(True, networks=[{"name": n["ssid"], "signal": n["signal"], "password": n["secure"],
                                       "connected": n["active"], "saved": n.get("saved", False)}
                                      for n in networks[:15]])
    if name == "connect_wifi":
        network = settings_helpers().Network(runner)
        known = {n["ssid"]: n for n in network.networks()}
        if a["name"] not in known:
            return answer(False, error="No Wi-Fi network of that name is in range.")
        ok = network.connect(a["name"], a.get("password", ""), known[a["name"]].get("security", ""))
        return answer(bool(ok), name=a["name"])
    if name == "set_wallpaper":
        path = Path(os.path.expanduser(a["path"]))
        if not path.is_file():
            return answer(False, error="The picture does not exist.")
        return answer(bool(settings_helpers().Personalization(runner).set_wallpaper(path)), path=str(path))
    if name == "set_timezone":
        return answer(bool(settings_helpers().Time(runner).set_timezone(a["zone"])), zone=a["zone"])
    if name == "power":
        starter(POWER_COMMANDS[a["action"]])
        return answer(True, action=a["action"])
    if name in ("install_app", "uninstall_app"):
        package = package_name(a["package"])
        if not package:
            return answer(False, error="Not a Debian package name.")
        if name == "uninstall_app":
            from veltos_store.packages import removal_is_protected
            if removal_is_protected(package):
                return answer(False, error="This package is part of VeltOS and cannot be removed.")
            ok, error = pkcon(["remove", package], runner)
            return answer(ok, package=package, **({"error": error} if error else {}))
        if lists_old():
            pkcon(["refresh"], runner)
        ok, error = pkcon(["install", package], runner)
        return answer(ok, package=package, **({"error": error} if error else {}))
    if name == "install_updates":
        pkcon(["refresh"], runner)
        ok, error = pkcon(["update"], runner)
        return answer(ok, **({"error": error} if error else {}))
    if name == "create_folder":
        path = home_path(a["path"], must_exist=False)
        if path is None:
            return answer(False, error="Folders can be created only inside the home folder.")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            return answer(False, error=str(error))
        return answer(True, path=str(path))
    if name == "move_to_recycle_bin":
        path = home_path(a["path"])
        if path is None or path == home().resolve():
            return answer(False, error="Only existing files and folders inside the home folder can be moved.")
        code, _ = runner(["gio", "trash", str(path)], timeout=120)
        return answer(code == 0, path=str(path))
    if name == "empty_recycle_bin":
        code, _ = runner(["ktrash6", "--empty"], timeout=300)
        return answer(code == 0)
    if name == "open_file":
        path = home_path(a["path"])
        if path is None:
            return answer(False, error="Only existing files inside the home folder can be opened.")
        starter(["xdg-open", str(path)])
        return answer(True, path=str(path))
    if name == "read_text_file":
        path = home_path(a["path"])
        if path is None or not path.is_file():
            return answer(False, error="Only existing files inside the home folder can be read.")
        try:
            data = path.read_bytes()[:MAX_READ * 4]
        except OSError as error:
            return answer(False, error=str(error))
        if b"\0" in data[:4096]:
            return answer(False, error="This is not a text file.")
        text = data.decode("utf-8", "replace")
        return answer(True, path=str(path), text=text[:MAX_READ], truncated=len(text) > MAX_READ)
    if name == "write_text_file":
        path = home_path(a["path"], must_exist=False)
        if path is None:
            return answer(False, error="Files can be written only inside the home folder.")
        if path.exists() and not a.get("overwrite"):
            return answer(False, error="The file exists; set overwrite to replace it.")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(a["text"], encoding="utf-8")
        except OSError as error:
            return answer(False, error=str(error))
        return answer(True, path=str(path))
    if name == "run_command":
        code, output = command_runner(a["command"], bool(a.get("administrator")))
        if a.get("administrator") and code in (126, 127) and not output.strip():
            return answer(False, exit_code=code, error="The administrator's password was not given.")
        return answer(code == 0, exit_code=code, output=output)
    return answer(False, error="Unknown action.")
