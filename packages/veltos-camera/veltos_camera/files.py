"""Where VeltOS Camera saves photos and videos, and what they are called.

Like Windows, photos and videos go to Pictures > Camera Roll ("Film
Rulosu" in Turkish, the name Windows uses there); the Pictures folder is
the user's XDG pictures directory (~/Resimler on Turkish systems).
Files are named like a phone camera's: IMG_20261021_093015.jpg,
VID_20261021_093015.mp4 (a number is added if the second is taken).
"""

import datetime
import os
import re
from pathlib import Path

ROLL_NAMES = {"en": "Camera Roll", "tr": "Film Rulosu"}
PHOTO_SUFFIXES = (".jpg", ".jpeg", ".png")
VIDEO_SUFFIXES = (".mp4", ".mkv", ".webm", ".mov")


def pictures_dir(home=None, config_home=None):
    """The user's Pictures folder (xdg-user-dirs), else ~/Pictures."""
    home = Path(home or Path.home())
    config_home = Path(config_home or os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    try:
        text = (config_home / "user-dirs.dirs").read_text(encoding="utf-8")
    except OSError:
        text = ""
    match = re.search(r'^XDG_PICTURES_DIR="([^"]*)"', text, re.MULTILINE)
    if match:
        value = match.group(1).replace("$HOME", str(home))
        if value.strip("/") and Path(value) != home:
            return Path(value)
    return home / "Pictures"


def camera_roll(lang="en", home=None, config_home=None):
    return pictures_dir(home, config_home) / ROLL_NAMES.get(lang, ROLL_NAMES["en"])


def new_path(folder, kind, now=None):
    """A free file name for a photo ("photo") or video ("video")."""
    now = now or datetime.datetime.now()
    prefix, suffix = ("IMG", ".jpg") if kind == "photo" else ("VID", ".mp4")
    stem = f"{prefix}_{now:%Y%m%d_%H%M%S}"
    path = Path(folder) / f"{stem}{suffix}"
    number = 1
    while path.exists():
        number += 1
        path = Path(folder) / f"{stem}_{number}{suffix}"
    return path


def latest_capture(folder):
    """The newest photo or video in the folder (path), or None."""
    try:
        entries = [p for p in Path(folder).iterdir()
                   if p.is_file() and p.suffix.lower() in PHOTO_SUFFIXES + VIDEO_SUFFIXES]
    except OSError:
        return None
    if not entries:
        return None
    return max(entries, key=lambda p: (p.stat().st_mtime, p.name))


def is_video(path):
    return Path(path).suffix.lower() in VIDEO_SUFFIXES
