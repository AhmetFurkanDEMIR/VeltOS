"""The Windows environment (Wine prefix) that Windows programs run in.

All programs share one environment, like the single C: drive of a Windows
PC: ~/.local/share/veltos/windows/ (prefix in prefix/). A per-program
environment was tried first and cost ~1.7 GB per program, because Wine
copies its own DLLs into every prefix (and Debian's carry debug info).

Records of installed programs live in records/<name>.json, logs in logs/.
"""

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

# Free space needed to create the environment (stripped prefix ~650 MB plus
# room for a program) and to install into an existing one.
SETUP_SPACE = 1500 * 1024 * 1024
INSTALL_SPACE = 300 * 1024 * 1024

# Registry defaults for a modern look: Wine's "Light" theme and smoothed
# fonts instead of the classic Windows 2000 style.
LOOK_REG = r'''REGEDIT4

[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\ThemeManager]
"ThemeActive"="1"
"DllName"="C:\\windows\\resources\\themes\\light\\light.msstyles"
"ColorName"="NormalColor"
"SizeName"="NormalSize"

[HKEY_CURRENT_USER\Control Panel\Desktop]
"FontSmoothing"="2"
"FontSmoothingType"=dword:00000002
"FontSmoothingGamma"=dword:00000578
"FontSmoothingOrientation"=dword:00000001
'''


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def apps_root():
    return data_home() / "veltos" / "windows"


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40].strip("-") or "app"


def wine_tool(name):
    """Debian installs Wine tools as e.g. wine-stable; plain names are alternatives."""
    for candidate in (name, f"{name}-stable"):
        if shutil.which(candidate):
            return candidate
    return name


def wine_version():
    try:
        return subprocess.run([wine_tool("wine"), "--version"], capture_output=True, text=True,
                              timeout=20).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def has_hardware_vulkan():
    """True if a real GPU offers Vulkan (DXVK on the CPU fallback would be slow)."""
    try:
        out = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True,
                             timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(kind in out for kind in ("PHYSICAL_DEVICE_TYPE_DISCRETE_GPU",
                                        "PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU"))


LIVE_RAM_RESERVE = 1536 * 1024 * 1024


def live_session():
    """Running from the install medium (RAM-backed storage, limited space)."""
    return Path("/run/live/medium").exists()


def memory_available():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0


class Environment:
    def __init__(self, root=None):
        self.root = root or apps_root()
        self.prefix = self.root / "prefix"
        self.logs = self.root / "logs"
        self.records = self.root / "records"
        self.marker = self.root / "prepared-for"

    @property
    def ready(self):
        """Created, and prepared (stripped, themed) for the installed Wine."""
        return (self.prefix / "system.reg").exists() and self.marker.exists() \
            and self.marker.read_text().strip() == wine_version()

    def free_space(self):
        probe = self.root if self.root.exists() else data_home()
        probe.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(probe).free
        if live_session():
            # On the install medium, files live in RAM (tmpfs overlay): what
            # can be written is also limited by available memory, minus a
            # reserve so the desktop itself keeps running.
            free = min(free, max(0, memory_available() - LIVE_RAM_RESERVE))
        return free

    def enough_space(self):
        needed = INSTALL_SPACE if self.ready else SETUP_SPACE
        return self.free_space() >= needed, needed

    def env(self, base=None):
        env = dict(os.environ if base is None else base)
        env.update({
            "WINEPREFIX": str(self.prefix),
            "WINEARCH": "win64",
            "WINEDEBUG": "-all",
            "DXVK_LOG_LEVEL": "none",
            "DXVK_STATE_CACHE_PATH": str(self.root / "shader-cache"),
        })
        return env

    def setup_env(self, base=None):
        """Environment for preparation steps: without a display, Wine creates
        the prefix silently instead of showing its own progress window."""
        env = self.env(base)
        env.pop("DISPLAY", None)
        # Wine 10 would otherwise use the default Wayland socket.
        env["WAYLAND_DISPLAY"] = "veltos-no-display"
        return env

    def write_setup_files(self):
        self.root.mkdir(parents=True, exist_ok=True)
        reg = self.root / "veltos-look.reg"
        reg.write_text(LOOK_REG, encoding="utf-8")
        return reg

    def setup_commands(self, vulkan):
        """Create or update the environment. Wine Mono/Gecko come from
        /usr/share/wine (veltos-wine-addons), so nothing is downloaded.
        Call write_setup_files() first and mark_prepared() after success."""
        patterns = " -o ".join(f"-iname '*.{ext}'" for ext in
                               ("dll", "exe", "drv", "sys", "cpl", "ocx", "acm"))

        def strip_cmd(folder, tool):
            return (f"cd '{self.prefix}/drive_c/windows' && [ -d {folder} ] && "
                    f"find {folder} -type f '(' {patterns} ')' "
                    f"-exec {tool} --strip-debug '{{}}' + 2>/dev/null; true")
        commands = [
            [wine_tool("wineboot"), "--init"],
            [wine_tool("wineserver"), "-w"],
            # Wine copies its DLLs into the prefix; Debian builds carry debug
            # info. Stripping the copies roughly halves the environment.
            ["sh", "-c", strip_cmd("system32", "x86_64-w64-mingw32-strip")],
            ["sh", "-c", strip_cmd("syswow64", "i686-w64-mingw32-strip")],
            [wine_tool("wine"), "regedit", "/S", str(self.root / "veltos-look.reg")],
        ]
        if vulkan:
            commands.append(["dxvk-setup", "install", "--yes"])
        commands.append([wine_tool("wineserver"), "-w"])
        return commands

    def mark_prepared(self):
        self.marker.write_text(wine_version() + "\n")

    def run_command(self, path, kind):
        if kind == "msi":
            return [wine_tool("wine"), "msiexec", "/i", str(path)]
        return [wine_tool("wine"), "start", "/wait", "/unix", str(path)]

    def wait_command(self):
        """Blocks until every Windows process in the environment has exited."""
        return [wine_tool("wineserver"), "-w"]

    def new_log(self):
        self.logs.mkdir(parents=True, exist_ok=True)
        return self.logs / time.strftime("%Y%m%d-%H%M%S.log")

    def save_record(self, name, **data):
        self.records.mkdir(parents=True, exist_ok=True)
        path = self.records / f"{slugify(name)}.json"
        data["name"] = name
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return path


def installed_apps(env=None):
    """Records of installed programs, newest first."""
    env = env or Environment()
    records = []
    for record in env.records.glob("*.json"):
        try:
            records.append(json.loads(record.read_text()))
        except (OSError, ValueError):
            continue
    return sorted(records, key=lambda r: r.get("installed_at", ""), reverse=True)
