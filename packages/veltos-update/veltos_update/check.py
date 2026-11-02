"""The daily check (`/usr/libexec/veltos/update-check`, a systemd user timer
of every user: veltos-update-check.timer, once a day, 15 minutes after
signing in when a day was missed):

  - the newest release from GitHub (release.py); when it is newer than the
    installed VeltOS and the user was not told about it yet, a Windows 11
    style notification "VeltOS 1.2 is ready" with "View update", which
    opens Settings > VeltOS Update;
  - otherwise, when Debian has updates for the PC (`pkcon get-updates`
    after `pkcon refresh`, which the signed-in user may do without a
    password), "Updates are ready" once a day.

What it found is kept in ~/.local/state/veltos/update.json, where VeltOS
Settings reads the last check. "Get notified" off in Settings
(~/.config/veltos/update.conf, `[Update] notify = false`) keeps the check
but not the notification. Without internet it ends quietly.
"""

import configparser
import json
import os
import time
from pathlib import Path

from . import release, steps


def state_path():
    return Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "veltos/update.json"


def user_conf():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "veltos/update.conf"


def load(path=None):
    try:
        data = json.loads(Path(path or state_path()).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(data, path=None):
    path = Path(path or state_path())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def notify_enabled(path=None):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path or user_conf(), encoding="utf-8")
    except (OSError, configparser.Error):
        return True
    return parser.getboolean("Update", "notify", fallback=True)


def set_notify(on, path=None):
    path = Path(path or user_conf())
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error):
        pass
    if not parser.has_section("Update"):
        parser.add_section("Update")
    parser.set("Update", "notify", "true" if on else "false")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            parser.write(fh)
    except OSError:
        return False
    return True


def other_updates(runner=steps.run):
    """(others, veltos): Debian's updates and VeltOS' own packages that
    PackageKit knows after a refresh."""
    runner(["pkcon", "-p", "refresh"], timeout=600)
    code, out = runner(["pkcon", "-p", "get-updates"], timeout=300)
    return steps.split_updates(out) if code in (0, 5) else (0, 0)


MIN_INTERVAL = 20 * 3600


def run(fetch=release.fetch, installed=release.installed_version, updates=other_updates, notify=None,
        now=None, state_file=None, conf=None, force=False):
    """One check. Returns what it told the user: "release", "updates" or ""
    ("" also when the last check is less than 20 hours old)."""
    now = time.time() if now is None else now
    state = load(state_file)
    if not force and 0 <= now - float(state.get("checked") or 0) < MIN_INTERVAL:
        return ""
    try:
        latest = fetch()
    except (OSError, ValueError):
        latest = None
    others, veltos = updates()
    count = others + veltos
    state.update(checked=now, others=others, veltos=veltos)
    if latest:
        state["latest"] = latest
    told = ""
    if notify_enabled(conf) and notify is not None:
        version = installed()
        if latest and release.newer(latest["version"], version) and state.get("notified") != latest["version"]:
            if notify("release", latest, count):
                state["notified"] = latest["version"]
                told = "release"
        elif count > 0 and state.get("notified_day") != time.strftime("%Y-%m-%d", time.localtime(now)):
            if notify("updates", latest, count):
                state["notified_day"] = time.strftime("%Y-%m-%d", time.localtime(now))
                told = "updates"
    save(state, state_file)
    return told
