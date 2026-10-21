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
