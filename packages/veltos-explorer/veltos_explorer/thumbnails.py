"""Picture thumbnails in the shared freedesktop.org cache
(~/.cache/thumbnails/{normal,large}), which KDE programs use too, so a
picture is scaled once for every program."""

import hashlib
import os
import urllib.parse
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader

PICTURE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp", "image/tiff",
                 "image/x-icon", "image/avif", "image/heif", "image/jxl"}


def cache_dir():
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "thumbnails"


def file_uri(path):
    return "file://" + urllib.parse.quote(str(path))


def thumbnail_path(path, large=False):
    digest = hashlib.md5(file_uri(path).encode("utf-8")).hexdigest()
    return cache_dir() / ("large" if large else "normal") / f"{digest}.png"


def cached(path, large=False):
    """The thumbnail file if it exists and matches the picture's time."""
    thumb = thumbnail_path(path, large)
    try:
        mtime = str(int(os.stat(path).st_mtime))
    except OSError:
        return ""
    if not thumb.exists():
        return ""
    image = QImageReader(str(thumb))
    if image.text("Thumb::MTime") not in ("", mtime):
        return ""
    return str(thumb)


def make(path, large=False):
    """Scale the picture and store the thumbnail; returns its file or ""."""
    size = 256 if large else 128
    try:
        st = os.stat(path)
    except OSError:
        return ""
    if st.st_size > 200 * 1024 ** 2:
        return ""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original = reader.size()
    if original.isValid() and (original.width() > size or original.height() > size):
        reader.setScaledSize(original.scaled(QSize(size, size), Qt.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        return ""
    image = image.convertToFormat(QImage.Format_ARGB32)
    image.setText("Thumb::URI", file_uri(path))
    image.setText("Thumb::MTime", str(int(st.st_mtime)))
    image.setText("Thumb::Size", str(st.st_size))
    thumb = thumbnail_path(path, large)
    thumb.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(thumb.parent, 0o700)
    temporary = thumb.with_suffix(f".{os.getpid()}.tmp")
    if not image.save(str(temporary), "PNG"):
        return ""
    os.chmod(temporary, 0o600)
    os.replace(temporary, thumb)
    return str(thumb)
