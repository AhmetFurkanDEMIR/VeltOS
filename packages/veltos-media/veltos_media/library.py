"""The music and videos of VeltOS Media Player: the folders (Music and
Videos, plus those the user adds), the songs with their tags and cover
pictures (mutagen), albums and artists, and the videos."""

import hashlib
import json
import os
from pathlib import Path

AUDIO_SUFFIXES = {".mp3", ".flac", ".ogg", ".oga", ".opus", ".m4a", ".aac", ".wav", ".wma", ".aiff", ".aif",
                  ".ape", ".mka"}
VIDEO_SUFFIXES = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".wmv", ".3gp", ".mpg", ".mpeg", ".ogv",
                  ".ts", ".flv"}
SKIP_DIRS = {".cache", ".Trash", ".git", "node_modules", "drive_c"}
COVER_NAMES = ("cover", "folder", "front", "album", "albumart")


# VeltOS' sample media (veltos-desktop: the wallpapers as pictures, a video
# and a song), part of the libraries as Windows' sample files were.
SAMPLES = Path("/usr/share/veltos/samples")


def sample_dirs(*names, root=None):
    """The sample folders that exist, as paths."""
    base = SAMPLES if root is None else Path(root)
    return [base / name for name in names if (base / name).is_dir()]


def user_dir(name, fallback):
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "user-dirs.dirs"
    try:
        for line in config.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"XDG_{name}_DIR="):
                return Path(line.split("=", 1)[1].strip().strip('"').replace("$HOME", str(home)))
    except OSError:
        pass
    return home / fallback


def kind_of(path):
    suffix = Path(path).suffix.lower()
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return ""


def _first(tags, *keys):
    for key in keys:
        value = tags.get(key)
        if value:
            if isinstance(value, (list, tuple)):
                value = value[0]
            text = str(value).strip()
            if text:
                return text
    return ""


def _number(text):
    try:
        return int(str(text).split("/")[0])
    except (TypeError, ValueError):
        return 0


def _cover_from_file(media, path, cover_dir):
    """The embedded cover picture, saved once into cover_dir."""
    data = None
    try:
        pictures = getattr(media, "pictures", None)          # FLAC
        if pictures:
            data = pictures[0].data
        elif media.tags is not None:
            for key in list(media.tags.keys()):
                if str(key).startswith("APIC"):              # MP3 (ID3)
                    data = media.tags[key].data
                    break
                if key == "covr":                            # MP4
                    data = bytes(media.tags[key][0])
                    break
                if str(key).lower() == "metadata_block_picture":   # Ogg Vorbis/Opus
                    import base64
                    from mutagen.flac import Picture
                    data = Picture(base64.b64decode(media.tags[key][0])).data
                    break
    except Exception:  # odd tags: no cover
        data = None
    if not data:
        return ""
    digest = hashlib.sha1(data).hexdigest()
    target = Path(cover_dir) / f"{digest}.jpg"
    if not target.exists():
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError:
            return ""
    return str(target)


def _cover_from_folder(path):
    folder = Path(path).parent
    try:
        for entry in folder.iterdir():
            if entry.stem.lower() in COVER_NAMES and entry.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                return str(entry)
    except OSError:
        pass
    return ""


def song(path, cover_dir):
    """A song's tags: title, artist, album, album artist, track, disc,
    year, genre, duration (seconds) and cover picture."""
    entry = {"path": str(path), "kind": "audio", "title": Path(path).stem, "artist": "", "album": "",
             "albumArtist": "", "track": 0, "disc": 0, "year": "", "genre": "", "duration": 0, "cover": ""}
    try:
        import mutagen
        easy = mutagen.File(path, easy=True)
        full = mutagen.File(path)
    except Exception:  # unreadable or unknown: name only
        easy = full = None
    if easy is not None:
        tags = easy.tags or {}
        if tags and ("TIT2" in tags or "TPE1" in tags):
            # Formats without "easy" tags (WAV, AIFF) give ID3 frames.
            frames = {"TIT2": "title", "TPE1": "artist", "TALB": "album", "TPE2": "albumartist",
                      "TRCK": "tracknumber", "TPOS": "discnumber", "TDRC": "date", "TCON": "genre"}
            tags = {name: [str(tags[frame].text[0])] for frame, name in frames.items()
                    if frame in tags and tags[frame].text}
        entry["title"] = _first(tags, "title") or entry["title"]
        entry["artist"] = _first(tags, "artist")
        entry["album"] = _first(tags, "album")
        entry["albumArtist"] = _first(tags, "albumartist") or entry["artist"]
        entry["track"] = _number(_first(tags, "tracknumber"))
        entry["disc"] = _number(_first(tags, "discnumber"))
        entry["year"] = _first(tags, "date", "year")[:4]
        entry["genre"] = _first(tags, "genre")
        info = getattr(easy, "info", None)
        entry["duration"] = int(getattr(info, "length", 0) or 0)
    if full is not None:
        entry["cover"] = _cover_from_file(full, path, cover_dir)
    if not entry["cover"]:
        entry["cover"] = _cover_from_folder(path)
    return entry


def video(path):
    entry = {"path": str(path), "kind": "video", "title": Path(path).stem, "duration": 0}
    try:
        import mutagen
        media = mutagen.File(path)
        if media is not None and getattr(media, "info", None) is not None:
            entry["duration"] = int(getattr(media.info, "length", 0) or 0)
    except Exception:  # containers mutagen does not know (MKV, WebM)
        pass
    return entry


def scan(music_folders, video_folders, cover_dir, cache=None):
    """(songs, videos) of the folders. `cache` maps path -> previous entry;
    entries of unchanged files are reused (tags are read once)."""
    cache = cache or {}
    songs, videos, seen = [], [], set()
    for folders, wanted in ((music_folders, "audio"), (video_folders, "video")):
        for folder in folders:
            for root, dirs, files in os.walk(folder, followlinks=False):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                for name in files:
                    kind = kind_of(name)
                    if not kind:
                        continue
                    path = os.path.join(root, name)
                    if path in seen:
                        continue
                    seen.add(path)
                    try:
                        st = os.stat(path)
                    except OSError:
                        continue
                    old = cache.get(path)
                    if old and old.get("mtime") == int(st.st_mtime) and old.get("size") == st.st_size:
                        entry = old
                    else:
                        entry = song(path, cover_dir) if kind == "audio" else video(path)
                        entry.update(mtime=int(st.st_mtime), size=st.st_size)
                    (songs if kind == "audio" else videos).append(entry)
    songs.sort(key=lambda s: (s["albumArtist"].lower(), s["album"].lower(), s["disc"], s["track"], s["title"].lower()))
    videos.sort(key=lambda v: -v.get("mtime", 0))
    return songs, videos


def albums(songs):
    """Albums: title, artist, year, cover and their songs, by name."""
    groups = {}
    for s in songs:
        key = (s["albumArtist"].lower(), s["album"].lower())
        group = groups.setdefault(key, {"title": s["album"], "artist": s["albumArtist"], "year": s["year"],
                                        "cover": s["cover"], "songs": []})
        group["songs"].append(s["path"])
        if not group["cover"]:
            group["cover"] = s["cover"]
    return sorted(groups.values(), key=lambda a: (a["title"].lower(), a["artist"].lower()))


def artists(songs):
    groups = {}
    for s in songs:
        name = s["albumArtist"] or s["artist"]
        group = groups.setdefault(name.lower(), {"name": name, "songs": [], "cover": s["cover"]})
        group["songs"].append(s["path"])
        if not group["cover"]:
            group["cover"] = s["cover"]
    return sorted(groups.values(), key=lambda a: a["name"].lower())


def load_cache(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {e["path"]: e for e in data if isinstance(e, dict) and "path" in e}
    except (OSError, ValueError, TypeError):
        return {}


def save_cache(path, entries):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entries), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def duration_text(seconds):
    seconds = int(seconds or 0)
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
