"""The accounts a polkit request may be answered with, with their names
and pictures, for the prompt."""

import grp
import os
import pwd
import re
import subprocess
from pathlib import Path

# Shown for accounts without a picture (veltos-desktop; the sign-in screen
# shows it too).
DEFAULT_PICTURE = "/usr/share/veltos/faces/default.png"
ACCOUNTS_ICONS = Path("/var/lib/AccountsService/icons")


def user_info(uid):
    try:
        entry = pwd.getpwuid(int(uid))
    except (KeyError, ValueError, OverflowError):
        return None
    real = entry.pw_gecos.split(",")[0].strip() or entry.pw_name
    return {"uid": entry.pw_uid, "name": entry.pw_name, "realName": real, "icon": picture_of(entry)}


def picture_of(entry):
    """The account picture AccountsService keeps (readable by everyone),
    else the user's own ~/.face.icon, else the VeltOS default."""
    candidates = [ACCOUNTS_ICONS / entry.pw_name, Path(entry.pw_dir) / ".face.icon", Path(entry.pw_dir) / ".face"]
    for path in candidates:
        try:
            if path.is_file() and os.access(path, os.R_OK):
                return str(path)
        except OSError:
            continue
    return DEFAULT_PICTURE if os.path.isfile(DEFAULT_PICTURE) else ""


def users_for(identities, me=None):
    """[{uid, name, realName, icon}] for polkit identities
    [("unix-user", {"uid": n}) | ("unix-group", {"gid": n})], the current
    user first (Windows asks the signed-in administrator for their own
    password)."""
    me = os.getuid() if me is None else me
    uids = []
    for kind, values in identities:
        if kind == "unix-user" and "uid" in values:
            uids.append(int(values["uid"]))
        elif kind == "unix-group" and "gid" in values:
            try:
                group = grp.getgrgid(int(values["gid"]))
            except (KeyError, ValueError, OverflowError):
                continue
            for member in group.gr_mem:
                try:
                    uids.append(pwd.getpwnam(member).pw_uid)
                except KeyError:
                    continue
            for entry in pwd.getpwall():
                if entry.pw_gid == group.gr_gid and 1000 <= entry.pw_uid < 60000:
                    uids.append(entry.pw_uid)
    seen, result = set(), []
    for uid in uids:
        if uid in seen:
            continue
        seen.add(uid)
        info = user_info(uid)
        if info is not None:
            result.append(info)
    result.sort(key=lambda u: (u["uid"] != me, u["uid"] == 0, u["realName"].casefold()))
    return result


# Where apps' desktop files are: VeltOS' renamed copies first (veltos-desktop).
APP_DIRS = ("/var/lib/veltos/xdg/applications", "/usr/local/share/applications", "/usr/share/applications")


def desktop_entry(path, lang="en"):
    """{name, icon} of a desktop file's [Desktop Entry] (name in `lang`)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    entry, values = False, {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            entry = line == "[Desktop Entry]"
        elif entry and "=" in line:
            key, _sep, value = line.partition("=")
            values.setdefault(key.strip(), value.strip())
    name = values.get(f"Name[{lang}]") or values.get("Name", "")
    return {"name": name, "icon": values.get("Icon", "")} if name else None


def requesting_app(details, lang="en", proc="/proc", app_dirs=APP_DIRS, depth=8):
    """The app that asked, as Windows' prompt names it with its icon: from
    the process polkit names (polkit.subject-pid, e.g. pkcon) up through its
    parents to the first one started from an app's desktop file
    (/usr/bin/veltos-store -> veltos-store.desktop). None if none is found;
    the prompt then shows the action's own icon."""
    pid = str(details.get("polkit.subject-pid") or "")
    for _ in range(depth):
        if not pid.isdigit() or int(pid) <= 1:
            return None
        try:
            args = Path(proc, pid, "cmdline").read_bytes().split(b"\0")
            stat = Path(proc, pid, "stat").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        for arg in args[:2]:
            base = os.path.basename(arg.decode("utf-8", "replace"))
            if not base or base.startswith("-"):
                continue
            for folder in app_dirs:
                found = desktop_entry(Path(folder) / f"{base}.desktop", lang)
                if found:
                    return found
        fields = stat.rsplit(")", 1)[-1].split()
        pid = fields[1] if len(fields) > 1 else ""      # the parent
    return None


def program_name(details):
    """A readable name of the program asking, from polkit's details
    (pkexec sends "program" and "command_line"; others usually nothing)."""
    for key in ("program", "command_line"):
        value = details.get(key)
        if value:
            return os.path.basename(value.split()[0]) if key == "command_line" else os.path.basename(value)
    return ""


def action_description(action_id, policy_dirs=("/usr/share/polkit-1/actions",), lang="en"):
    """The action's description from its .policy file ("" if unknown)."""
    vendor, _sep, _rest = action_id.rpartition(".")
    for folder in policy_dirs:
        for path in sorted(Path(folder).glob("*.policy")) if Path(folder).is_dir() else []:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            match = re.search(r'<action id="%s">(.*?)</action>' % re.escape(action_id), text, re.S)
            if not match:
                continue
            block = match.group(1)
            localized = re.search(r'<description xml:lang="%s">(.*?)</description>' % lang, block, re.S)
            plain = re.search(r"<description>(.*?)</description>", block, re.S)
            chosen = localized or plain
            if chosen:
                return re.sub(r"\s+", " ", chosen.group(1)).strip()
    return ""


def run_output(command, timeout=5):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
