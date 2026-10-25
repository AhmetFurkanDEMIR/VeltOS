"""What VeltOS AI may do on the computer: a fixed list of actions, never
a shell. Looking things up (the PC's details, file names) runs at once;
everything that changes something or opens something waits for the
user's "Allow" in the panel, as Copilot asks on Windows 11. The changes go
through the same helpers as VeltOS Settings (light/dark, volume, Wi-Fi,
Bluetooth), so they behave the same.

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
from pathlib import Path

from . import strings

SETTINGS_PAGES = ("home", "system", "display", "sound", "notifications", "power", "storage", "about",
                  "bluetooth", "devices", "mouse", "keyboard", "network", "wifi", "personalization", "background",
                  "colors", "themes", "lockscreen", "taskbar", "apps", "defaultapps", "startup", "windows-apps",
                  "accounts", "yourinfo", "signin", "time", "datetime", "region", "gaming", "accessibility",
                  "privacy", "update")
FOLDERS = ("home", "desktop", "documents", "downloads", "pictures", "music", "videos", "this_pc", "recycle_bin")
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
    {"name": "open_app", "description": "Open an installed app by its name as shown in Start (for example "
     "\"File Explorer\", \"Notepad\", \"Calculator\", \"Firefox\", \"Word\").",
     "parameters": obj({"name": {"type": "string", "description": "The app's name"}}, ["name"])},
    {"name": "open_settings", "description": "Open a page of VeltOS Settings.",
     "parameters": obj({"page": {"type": "string", "enum": list(SETTINGS_PAGES)}}, ["page"])},
    {"name": "set_theme", "description": "Switch the whole system between light and dark mode.",
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
    {"name": "take_screenshot", "description": "Start Snipping Tool to take a screenshot (the user picks the "
     "area).", "parameters": obj()},
]
BY_NAME = {tool["name"]: tool for tool in TOOLS}
READ_ONLY = ("get_system_info", "search_files")


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


def find_app(name, lang="en", dirs=None):
    """(desktop file, shown name) of the app whose name fits best, or None."""
    wanted = name.casefold().strip()
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
                folded = candidate.casefold()
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


def execute(name, arguments, lang="en", starter=start, runner=run):
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
    return answer(False, error="Unknown action.")
