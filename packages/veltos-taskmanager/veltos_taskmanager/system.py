"""What VeltOS Task Manager shows: processes grouped like Windows (apps,
background processes, system processes), system performance, start-up apps.

Data comes from psutil (Debian: python3-psutil) and the freedesktop .desktop
files; everything that touches the system is passed in, so the tests run
with recorded data.
"""

import configparser
import os
import shlex
import signal
import time
from pathlib import Path

APPLICATION_DIRS = [Path("/var/lib/veltos/xdg/applications"), Path("/usr/local/share/applications"),
                    Path("/usr/share/applications")]
AUTOSTART_SYSTEM = Path("/etc/xdg/autostart")

# Interpreters and wrappers: the program is in the arguments, not the binary.
WRAPPERS = {"python3", "python", "sh", "bash", "env", "perl", "flatpak", "wine", "wine64",
            "wine-preloader", "wine64-preloader"}


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def read_desktop(path):
    """The [Desktop Entry] group of a .desktop file as a dict ({} if unreadable)."""
    parser = configparser.RawConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return {}
    return dict(parser["Desktop Entry"]) if parser.has_section("Desktop Entry") else {}


def localized(entry, key, lang):
    return entry.get(f"{key}[{lang}]") or entry.get(key, "")


def exec_name(exec_line):
    """The program a desktop file starts: "env FOO=1 /usr/bin/x %U" -> "x"."""
    try:
        words = shlex.split(exec_line)
    except ValueError:
        words = exec_line.split()
    for word in words:
        if word == "env" or "=" in word and not word.startswith("/"):
            continue
        return os.path.basename(word)
    return ""


class AppIndex:
    """Installed applications by the program they start (and StartupWMClass),
    so a running process can be shown with the app's name and icon."""

    def __init__(self, dirs=None, lang="en"):
        self.by_program = {}
        for directory in (dirs or APPLICATION_DIRS):
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.desktop")):
                entry = read_desktop(path)
                if not entry or entry.get("Type", "Application") != "Application":
                    continue
                app = {"id": path.name, "name": localized(entry, "Name", lang) or path.stem,
                       "icon": entry.get("Icon", "application-x-executable"),
                       "hidden": entry.get("NoDisplay", "").lower() == "true"}
                for program in {exec_name(entry.get("Exec", "")), entry.get("StartupWMClass", "").lower()}:
                    # The first directory wins (VeltOS names before the originals).
                    if program and program not in self.by_program:
                        self.by_program[program] = app

    def lookup(self, program):
        return self.by_program.get(program) or self.by_program.get(program.lower())


def program_of(name, cmdline):
    """The program a process runs: for interpreters, the script; the full
    name when the kernel's process name is cut to 15 characters
    ("veltos-taskman" for veltos-taskmanager)."""
    first = os.path.basename(cmdline[0]) if cmdline else ""
    if cmdline and (name in WRAPPERS or first in WRAPPERS or first.startswith("python3")):
        for arg in cmdline[1:]:
            if not arg.startswith("-"):
                return os.path.basename(arg)
    if first and first != name and first.startswith(name):
        return first
    return name


class Processes:
    """Process snapshots with CPU use since the previous snapshot."""

    def __init__(self, psutil_module=None, apps=None, uid=None):
        if psutil_module is None:
            import psutil as psutil_module
        self.ps = psutil_module
        self.apps = apps if apps is not None else AppIndex()
        self.uid = os.getuid() if uid is None else uid
        self._known = {}        # pid -> psutil.Process (keeps cpu_percent state)

    def snapshot(self):
        """List of dicts: pid, ppid, name, program, user (bool), cpu (% of all
        CPUs), memory (bytes), app (dict or None)."""
        cpus = self.ps.cpu_count() or 1
        seen = {}
        rows = []
        for proc in self.ps.process_iter(["pid", "ppid", "name", "cmdline", "uids", "memory_info"]):
            info = proc.info
            pid = info["pid"]
            known = self._known.get(pid)
            if known is None:
                known = proc
                try:
                    known.cpu_percent(None)       # starts the measurement
                except (self.ps.NoSuchProcess, self.ps.AccessDenied):
                    continue
                cpu = 0.0
            else:
                try:
                    cpu = known.cpu_percent(None) / cpus
                except (self.ps.NoSuchProcess, self.ps.AccessDenied):
                    continue
            seen[pid] = known
            program = program_of(info.get("name") or "", info.get("cmdline") or [])
            uids = info.get("uids")
            memory = info.get("memory_info")
            rows.append({
                "pid": pid,
                "ppid": info.get("ppid") or 0,
                "name": info.get("name") or str(pid),
                "program": program,
                "user": bool(uids) and uids.real == self.uid,
                "cpu": max(0.0, cpu),
                "memory": memory.rss if memory else 0,
                "app": self.apps.lookup(program),
                # Kernel threads have no command line and no memory of their own.
                "kernel": not (info.get("cmdline") or []) and not (memory and memory.rss),
            })
        self._known = seen
        return rows


def group(rows, lang="en"):
    """Windows' three groups. An app is the topmost process of a visible
    application with its descendants of the same user; its CPU and memory
    (and GPU share) are the sums. Returns {"apps": [...], "background": [...], "system": [...]},
    each entry: key, name, icon, pids, cpu, memory, count."""
    by_pid = {row["pid"]: row for row in rows}
    children = {}
    for row in rows:
        children.setdefault(row["ppid"], []).append(row)

    def is_app_root(row):
        app = row["app"]
        if not row["user"] or not app or app["hidden"]:
            return False
        parent = by_pid.get(row["ppid"])
        return not (parent and parent["app"] is app)

    taken = set()
    apps = {}
    for row in sorted(rows, key=lambda r: r["pid"]):
        if row["pid"] in taken or not is_app_root(row):
            continue
        key = row["app"]["id"]
        entry = apps.setdefault(key, {"key": key, "name": row["app"]["name"], "icon": row["app"]["icon"],
                                      "pids": [], "cpu": 0.0, "memory": 0, "gpu": 0.0})
        stack = [row]
        while stack:
            current = stack.pop()
            if current["pid"] in taken or not current["user"]:
                continue
            taken.add(current["pid"])
            entry["pids"].append(current["pid"])
            entry["cpu"] += current["cpu"]
            entry["memory"] += current["memory"]
            entry["gpu"] = min(100.0, entry["gpu"] + current.get("gpu", 0.0))
            stack.extend(children.get(current["pid"], []))
    background, system = [], []
    for row in rows:
        if row["pid"] in taken or row["pid"] == 0 or row.get("kernel"):
            continue
        app = row["app"]
        entry = {"key": f"pid:{row['pid']}", "name": (app["name"] if app else row["program"]),
                 "icon": (app["icon"] if app else "application-x-executable"),
                 "pids": [row["pid"]], "cpu": row["cpu"], "memory": row["memory"], "gpu": row.get("gpu", 0.0)}
        (background if row["user"] else system).append(entry)
    result = {}
    for name, items in (("apps", list(apps.values())), ("background", background), ("system", system)):
        for item in items:
            item["count"] = len(item["pids"])
        result[name] = sorted(items, key=lambda i: i["name"].lower())
    return result


def end_task(pids, psutil_module=None, wait=3.0):
    """Ask the processes to close (SIGTERM), then kill those still running."""
    if psutil_module is None:
        import psutil as psutil_module
    procs = []
    for pid in pids:
        try:
            proc = psutil_module.Process(pid)
            proc.send_signal(signal.SIGTERM)
            procs.append(proc)
        except (psutil_module.NoSuchProcess, psutil_module.AccessDenied):
            continue
    _gone, alive = psutil_module.wait_procs(procs, timeout=wait)
    for proc in alive:
        try:
            proc.kill()
        except (psutil_module.NoSuchProcess, psutil_module.AccessDenied):
            pass
    return len(procs)


def human_bytes(value, lang="en"):
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            text = f"{size:.0f} {unit}" if unit in ("B", "KB") else f"{size:.1f} {unit}"
            return text.replace(".", ",") if lang == "tr" else text
        size /= 1024
    return str(value)


def cpu_model(cpuinfo=Path("/proc/cpuinfo")):
    try:
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


class Performance:
    """System-wide figures, with rates since the previous sample."""

    def __init__(self, psutil_module=None, clock=time.monotonic):
        if psutil_module is None:
            import psutil as psutil_module
        self.ps = psutil_module
        self.clock = clock
        self._last = None

    def sample(self):
        now = self.clock()
        disk = self.ps.disk_io_counters()
        net = self.ps.net_io_counters()
        mem = self.ps.virtual_memory()
        freq = self.ps.cpu_freq()
        result = {
            "cpu": float(self.ps.cpu_percent(None)),
            "cpuSpeed": float(freq.current) if freq else 0.0,
            "cores": self.ps.cpu_count(logical=False) or 0,
            "threadsLogical": self.ps.cpu_count() or 0,
            "memoryTotal": mem.total,
            "memoryUsed": mem.total - mem.available,
            "memoryAvailable": mem.available,
            "memory": float(mem.percent),
            "uptime": max(0.0, time.time() - self.ps.boot_time()),
            "diskRead": 0.0, "diskWrite": 0.0, "netSent": 0.0, "netReceived": 0.0, "disk": 0.0,
        }
        if self._last is not None:
            then, old_disk, old_net = self._last
            span = max(1e-3, now - then)
            if disk and old_disk:
                result["diskRead"] = (disk.read_bytes - old_disk.read_bytes) / span
                result["diskWrite"] = (disk.write_bytes - old_disk.write_bytes) / span
                busy = getattr(disk, "busy_time", None)
                old_busy = getattr(old_disk, "busy_time", None)
                if busy is not None and old_busy is not None:
                    result["disk"] = min(100.0, max(0.0, (busy - old_busy) / (span * 10)))
            if net and old_net:
                result["netSent"] = (net.bytes_sent - old_net.bytes_sent) / span
                result["netReceived"] = (net.bytes_recv - old_net.bytes_recv) / span
        self._last = (now, disk, net)
        return result


def uptime_text(seconds):
    seconds = int(seconds)
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{days}:{hours:02d}:{minutes:02d}:{secs:02d}"


class StartupApps:
    """Autostart entries (freedesktop) with Windows' Enabled/Disabled state.
    Disabling writes a user copy with Hidden=true; enabling removes it (or
    sets Hidden=false for the user's own entries)."""

    def __init__(self, system_dir=AUTOSTART_SYSTEM, user_dir=None, lang="en"):
        self.system_dir = system_dir
        self.user_dir = user_dir or config_home() / "autostart"
        self.lang = lang

    def _entries(self):
        files = {}
        for directory in (self.system_dir, self.user_dir):
            if directory.is_dir():
                for path in sorted(directory.glob("*.desktop")):
                    files[path.name] = path
        return files

    def list(self):
        result = []
        for name, path in sorted(self._entries().items()):
            entry = read_desktop(path)
            system_entry = read_desktop(self.system_dir / name) if (self.system_dir / name).exists() else entry
            if not entry or system_entry.get("NoDisplay", "").lower() == "true":
                continue          # session internals, not apps
            only = system_entry.get("OnlyShowIn", "")
            if only and "KDE" not in only.split(";"):
                continue
            if "KDE" in system_entry.get("NotShowIn", "").split(";"):
                continue
            result.append({"id": name, "name": localized(system_entry, "Name", self.lang) or name,
                           "icon": system_entry.get("Icon", "application-x-executable"),
                           "enabled": entry.get("Hidden", "").lower() != "true"})
        return sorted(result, key=lambda e: e["name"].lower())

    def set_enabled(self, name, enabled):
        if "/" in name or not name.endswith(".desktop"):
            raise ValueError(name)
        user = self.user_dir / name
        system = self.system_dir / name
        if enabled:
            if system.exists() and user.exists() and read_desktop(user).get("Hidden", "").lower() == "true":
                user.unlink()
                return
            if user.exists():
                text = user.read_text(encoding="utf-8")
                user.write_text(text.replace("Hidden=true", "Hidden=false"), encoding="utf-8")
            return
        self.user_dir.mkdir(parents=True, exist_ok=True)
        source = user if user.exists() else system
        text = source.read_text(encoding="utf-8") if source.exists() else "[Desktop Entry]\n"
        lines = [line for line in text.splitlines() if not line.startswith("Hidden=")]
        out, inserted = [], False
        for line in lines:
            out.append(line)
            if line.strip() == "[Desktop Entry]" and not inserted:
                out.append("Hidden=true")
                inserted = True
        user.write_text("\n".join(out) + "\n", encoding="utf-8")
