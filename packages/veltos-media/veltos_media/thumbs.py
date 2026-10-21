"""Thumbnails in the shared freedesktop.org cache (~/.cache/thumbnails), so
a picture or video is scaled once for every program: pictures with Qt's
image reader, videos with ffmpegthumbnailer (a frame at 10 %)."""

import hashlib
import os
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader

SIZES = {"normal": 128, "large": 256, "x-large": 512}


def cache_dir():
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "thumbnails"


def file_uri(path):
    return "file://" + urllib.parse.quote(str(path))


def thumbnail_path(path, flavour="large"):
    digest = hashlib.md5(file_uri(path).encode("utf-8")).hexdigest()
    return cache_dir() / flavour / f"{digest}.png"


def cached(path, flavour="large"):
    """The thumbnail if it exists and is as new as the file, else ""."""
    thumb = thumbnail_path(path, flavour)
    try:
        mtime = str(int(os.stat(path).st_mtime))
    except OSError:
        return ""
    if not thumb.exists():
        return ""
    if QImageReader(str(thumb)).text("Thumb::MTime") not in ("", mtime):
        return ""
    return str(thumb)


def _store(image, path, flavour):
    try:
        mtime = str(int(os.stat(path).st_mtime))
    except OSError:
        return ""
    image.setText("Thumb::URI", file_uri(path))
    image.setText("Thumb::MTime", mtime)
    image.setText("Software", "VeltOS")
    thumb = thumbnail_path(path, flavour)
    try:
        thumb.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(suffix=".png", dir=str(thumb.parent))
        os.close(fd)
        if not image.save(tmp, "PNG"):
            os.unlink(tmp)
            return ""
        os.chmod(tmp, 0o600)
        os.replace(tmp, thumb)
    except OSError:
        return ""
    return str(thumb)


def picture(path, flavour="large"):
    size = SIZES[flavour]
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original = reader.size()
    if original.isValid() and (original.width() > size or original.height() > size):
        reader.setScaledSize(original.scaled(QSize(size, size), Qt.KeepAspectRatio))
    image = reader.read()
    return image


def video(path, flavour="large"):
    size = SIZES[flavour]
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        subprocess.run(["ffmpegthumbnailer", "-i", str(path), "-o", tmp, "-s", str(size), "-t", "10%",
                        "-c", "png"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
                       check=False)
        image = QImage(tmp)
    except (OSError, subprocess.SubprocessError):
        image = QImage()
    finally:
        Path(tmp).unlink(missing_ok=True)
    return image


def thumbnail(path, kind="image", flavour="large"):
    """A QImage thumbnail of a file, from the cache or made now (and
    stored). Null if the file cannot be read."""
    existing = cached(path, flavour)
    if existing:
        image = QImage(existing)
        if not image.isNull():
            return image
    try:
        if os.stat(path).st_size > 300 * 1024 ** 2 and kind == "image":
            return QImage()
    except OSError:
        return QImage()
    image = video(path, flavour) if kind == "video" else picture(path, flavour)
    if not image.isNull():
        _store(image, path, flavour)
    return image
