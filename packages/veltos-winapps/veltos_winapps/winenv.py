"""Private Windows environments (Wine prefixes) for Windows programs.

Every installed program gets its own environment under
~/.local/share/veltos/windows-apps/<name>/ so programs cannot break each
other and removing one removes everything it installed. Programs that need
no installation share one environment ("shared").
"""

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

SHARED = "shared"


def data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")


def apps_root():
    return data_home() / "veltos" / "windows-apps"


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40].strip("-") or "app"


def wine_tool(name):
    """Debian installs Wine tools as e.g. wine-stable; plain names are alternatives."""
    for candidate in (name, f"{name}-stable"):
        if shutil.which(candidate):
            return candidate
    return name


def has_hardware_vulkan():
    """True if a real GPU offers Vulkan (DXVK on the CPU fallback would be slow)."""
    try:
        out = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True,
                             timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(kind in out for kind in ("PHYSICAL_DEVICE_TYPE_DISCRETE_GPU",
                                        "PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU"))


class Environment:
    def __init__(self, slug):
        self.slug = slug
        self.root = apps_root() / slug
        self.prefix = self.root / "prefix"
        self.logs = self.root / "logs"

    @classmethod
    def for_new_app(cls, name):
        base = slugify(name)
        slug, n = base, 2
        while (apps_root() / slug).exists() or slug == SHARED:
            slug, n = f"{base}-{n}", n + 1
        return cls(slug)

    @classmethod
    def shared(cls):
        return cls(SHARED)

    @property
    def ready(self):
        return (self.prefix / "system.reg").exists()

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

    def setup_commands(self, vulkan):
        """Commands that create the environment (Wine Mono/Gecko come from
        /usr/share/wine, installed by veltos-wine-addons, without downloads)."""
        commands = [[wine_tool("wineboot"), "--init"]]
        if vulkan:
            commands.append(["dxvk-setup", "install", "--yes"])
        return commands

    def run_command(self, path, kind):
        if kind == "msi":
            return [wine_tool("wine"), "msiexec", "/i", str(path)]
        return [wine_tool("wine"), "start", "/wait", "/unix", str(path)]

    def wait_command(self):
        """Blocks until every process in this environment has exited."""
        return [wine_tool("wineserver"), "-w"]

    def new_log(self):
        self.logs.mkdir(parents=True, exist_ok=True)
        return self.logs / time.strftime("%Y%m%d-%H%M%S.log")

    def save_record(self, **data):
        self.root.mkdir(parents=True, exist_ok=True)
        record = self.root / "app.json"
        existing = json.loads(record.read_text()) if record.exists() else {}
        existing.update(data)
        record.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")


def installed_apps():
    """Records of all environments, newest first."""
    records = []
    for record in apps_root().glob("*/app.json"):
        try:
            data = json.loads(record.read_text())
        except (OSError, ValueError):
            continue
        data["slug"] = record.parent.name
        records.append(data)
    return sorted(records, key=lambda r: r.get("installed_at", ""), reverse=True)
