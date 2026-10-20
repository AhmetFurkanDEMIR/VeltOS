"""Apps > Default apps and Apps > Startup, from the desktop entries.

Default apps follow the freedesktop way: ~/.config/mimeapps.list. Startup apps are the autostart entries; turning
one off writes a copy with Hidden=true into ~/.config/autostart, turning
it on again removes that copy (or the Hidden key of the user's own entry).
"""

import os
import re
from pathlib import Path

from .devices import run


def data_dirs():
    home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    system = [Path(p) for p in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if p]
    # VeltOS' renamed copies (update-app-names) come first, as in the session.
    veltos = Path("/var/lib/veltos/xdg")
    if veltos not in system:
        system.insert(0, veltos)
    return [home, *system]


def application_dirs(dirs=None):
    return [d / "applications" for d in (dirs or data_dirs())]


def desktop_entry(path):
    """The [Desktop Entry] keys of a .desktop file ({} if unreadable)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    values, group = {}, None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            group = line
        elif group == "[Desktop Entry]" and "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip())
    return values


def localized(values, key, lang):
    return values.get(f"{key}[{lang}]") or values.get(key, "")


def find_desktop(entry, app_dirs=None):
    name = entry if entry.endswith(".desktop") else entry + ".desktop"
    for folder in app_dirs or application_dirs():
        path = folder / name
        if path.is_file():
            return path
    return None


def desktop_info(entry, app_dirs=None, lang="en"):
    """Name and icon of an installed app (None if it is not installed)."""
    path = find_desktop(entry, app_dirs)
    if path is None:
        return None
    values = desktop_entry(path)
    if not values:
        return None
    return {"name": localized(values, "Name", lang) or entry, "icon": values.get("Icon", "application-x-executable")}


# --- Default apps ---------------------------------------------------------------------

# Windows' "Default apps" groups: (id, English, Turkish, MIME types).
DEFAULT_GROUPS = [
    ("browser", "Web browser", "Web tarayıcısı",
     ["x-scheme-handler/http", "x-scheme-handler/https", "text/html", "application/xhtml+xml"]),
    ("email", "Email", "E-posta", ["x-scheme-handler/mailto"]),
    ("music", "Music player", "Müzik çalar", ["audio/mpeg", "audio/flac", "audio/x-vorbis+ogg", "audio/mp4"]),
    ("video", "Video player", "Video oynatıcı", ["video/mp4", "video/x-matroska", "video/webm", "video/x-msvideo"]),
    ("photos", "Photo viewer", "Fotoğraf görüntüleyici", ["image/jpeg", "image/png", "image/gif", "image/webp"]),
    ("pdf", "PDF reader", "PDF okuyucu", ["application/pdf"]),
    ("text", "Text editor", "Metin düzenleyici", ["text/plain"]),
]


def all_desktop_files(app_dirs=None):
    """Visible applications: desktop file name -> keys (first one wins)."""
    seen = {}
    for folder in app_dirs or application_dirs():
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.desktop")):
            if path.name in seen:
                continue
            values = desktop_entry(path)
            seen[path.name] = values
    return {name: values for name, values in seen.items()
            if values and values.get("NoDisplay", "false").lower() != "true"
            and values.get("Hidden", "false").lower() != "true"
            and values.get("Type", "Application") == "Application"}


def config_files(name):
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    system = [Path(p) for p in (os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":") if p]
    return [d / f for d in [home, *system] for f in (f"kde-{name}", name)]


def list_values(path, group):
    """{key: [values]} of one group of a mimeapps.list style file."""
    values, current = {}, None
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            current = line[1:-1]
        elif current == group and "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), [v for v in value.strip().split(";") if v])
    return values


def set_list_value(path, group, key, value):
    """Set key=value in a group of an ini file, keeping everything else."""
    path = Path(path)
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = []
    out, current, done = [], None, False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            if current == group and not done:
                out.append(f"{key}={value}")
                done = True
            current = stripped[1:-1]
        elif current == group and stripped.split("=", 1)[0].strip() == key:
            if not done:
                out.append(f"{key}={value}")
                done = True
            continue
        out.append(line)
    if not done:
        if current != group:
            if out and out[-1].strip():
                out.append("")
            out.append(f"[{group}]")
        out.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


class DefaultApps:
    """Default apps from the mimeapps.list files (as KDE reads them) and
    mimeinfo.cache. Read and written directly: Debian 13's `xdg-mime query`
    failed for text/plain in a Plasma session (VM, 2026-10-20)."""

    def __init__(self, runner=run, app_dirs=None, lang="en"):
        self.run = runner
        self.app_dirs = app_dirs
        self.lang = lang

    def _installed(self, name):
        return find_desktop(name, self.app_dirs or application_dirs()) is not None

    def current(self, mime):
        """The app that opens `mime` now ("" if none is set or installed)."""
        for path in config_files("mimeapps.list") + [d / "mimeapps.list" for d in self.app_dirs or application_dirs()]:
            for name in list_values(path, "Default Applications").get(mime, []):
                if self._installed(name):
                    return name
        for folder in self.app_dirs or application_dirs():
            for name in list_values(folder / "mimeinfo.cache", "MIME Cache").get(mime, []):
                if self._installed(name):
                    return name
        return ""

    def candidates(self, mime):
        """Apps that open `mime`. An app may handle a type through a hidden
        helper entry (Okular: okularApplication_pdf.desktop); it is offered
        under the visible app's name and icon."""
        visible = all_desktop_files(self.app_dirs)
        by_program = {}
        for name, values in visible.items():
            program = Path((values.get("Exec", "").split() or [""])[0]).name
            if program:
                by_program.setdefault(program, (name, values))
        result, seen = [], set()
        for folder in self.app_dirs or application_dirs():
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.desktop")):
                if path.name in seen:
                    continue
                seen.add(path.name)
                values = desktop_entry(path)
                if mime not in values.get("MimeType", "").split(";"):
                    continue
                if path.name in visible:
                    shown = values
                else:
                    program = Path((values.get("Exec", "").split() or [""])[0]).name
                    if program not in by_program or values.get("Hidden", "").lower() == "true":
                        continue
                    shown = by_program[program][1]
                result.append({"value": path.name, "label": localized(shown, "Name", self.lang) or path.name,
                               "icon": shown.get("Icon", "application-x-executable")})
        labels = {}
        for option in result:                       # one entry per app name
            labels.setdefault(option["label"], option)
        return sorted(labels.values(), key=lambda c: c["label"].lower())

    def state(self):
        groups = []
        for group_id, english, turkish, mimes in DEFAULT_GROUPS:
            options = self.candidates(mimes[0])
            current = self.current(mimes[0])
            if current and current not in [o["value"] for o in options]:
                current = ""
            groups.append({"id": group_id, "title": turkish if self.lang == "tr" else english,
                           "options": options, "current": current})
        return {"groups": groups}

    def set_default(self, group_id, desktop):
        for gid, _en, _tr, mimes in DEFAULT_GROUPS:
            if gid != group_id:
                continue
            if not re.fullmatch(r"[A-Za-z0-9._-]+\.desktop", desktop) or not self._installed(desktop):
                return False
            target = config_files("mimeapps.list")[1]       # ~/.config/mimeapps.list
            for mime in mimes:
                set_list_value(target, "Default Applications", mime, desktop + ";")
            return True
        return False


# --- Startup apps ---------------------------------------------------------------------

def autostart_dirs():
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "autostart"
    system = [Path(p) / "autostart"
              for p in (os.environ.get("XDG_CONFIG_DIRS") or "/etc/xdg").split(":") if p]
    return home, system


def _shown_in_kde(values):
    only = [v for v in values.get("OnlyShowIn", "").split(";") if v]
    never = [v for v in values.get("NotShowIn", "").split(";") if v]
    return (not only or "KDE" in only) and "KDE" not in never


class StartupApps:
    """Programs that start when the user signs in (not the desktop's own
    services, which have no visible app entry)."""

    def __init__(self, dirs=None, lang="en", app_dirs=None):
        self.home, self.system = dirs or autostart_dirs()
        self.lang = lang
        self.app_dirs = app_dirs

    def entries(self):
        found = {}
        for folder in [self.home, *self.system]:
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.desktop")):
                if path.name not in found:
                    found[path.name] = path
        result = []
        for name, path in found.items():
            values = desktop_entry(path)
            if not values or not _shown_in_kde(values):
                continue
            system_copy = next((d / name for d in self.system if (d / name).is_file()), None)
            # Desktop services (NoDisplay entries from the system) are not
            # apps the user started; Windows does not list them either.
            base = desktop_entry(system_copy) if system_copy else values
            if base.get("NoDisplay", "false").lower() == "true" or "X-KDE-autostart-phase" in base:
                continue
            enabled = values.get("Hidden", "false").lower() != "true" and \
                values.get("X-GNOME-Autostart-enabled", "true").lower() != "false"
            result.append({"id": name, "name": localized(values, "Name", self.lang) or name,
                           "icon": values.get("Icon", "application-x-executable"), "enabled": enabled})
        return sorted(result, key=lambda e: e["name"].lower())

    def set_enabled(self, entry_id, enabled):
        if not re.fullmatch(r"[A-Za-z0-9._-]+\.desktop", entry_id):
            return False
        user = self.home / entry_id
        system_copy = next((d / entry_id for d in self.system if (d / entry_id).is_file()), None)
        if enabled:
            if system_copy is not None and user.is_file():
                user.unlink()                       # the system entry applies again
            elif user.is_file():
                text = user.read_text(encoding="utf-8", errors="replace")
                text = re.sub(r"^Hidden=.*\n?", "", text, flags=re.M)
                user.write_text(text, encoding="utf-8")
            return True
        source = user if user.is_file() else system_copy
        if source is None:
            return False
        text = source.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"^Hidden=.*\n?", "", text, flags=re.M)
        text = re.sub(r"^\[Desktop Entry\]\s*$", "[Desktop Entry]\nHidden=true", text, count=1, flags=re.M)
        self.home.mkdir(parents=True, exist_ok=True)
        user.write_text(text, encoding="utf-8")
        return True
