"""Text files as Windows 11 Notepad handles them: the encoding (UTF-8, UTF-8
with BOM, UTF-16 LE/BE, ANSI) and the line endings (Windows CRLF, Unix LF,
Macintosh CR) are detected when a file is opened, shown in the status bar
and kept when it is saved. The editor itself always works with "\\n".
"""

import codecs
import os
import tempfile
from pathlib import Path

ENCODINGS = ("UTF-8", "UTF-8 with BOM", "UTF-16 LE", "UTF-16 BE", "ANSI")
EOLS = {"CRLF": "\r\n", "LF": "\n", "CR": "\r"}
# Notepad refuses files it cannot show in a reasonable time; Windows 11's
# limit is far higher, VeltOS keeps the editor responsive.
MAX_BYTES = 64 * 1024 * 1024


def ansi_codec(lang):
    """The "ANSI" code page of Windows for the user's language."""
    return "cp1254" if lang == "tr" else "cp1252"


def detect_encoding(data):
    """(encoding name, bytes to skip) for the start of a file."""
    if data.startswith(codecs.BOM_UTF8):
        return "UTF-8 with BOM", 3
    if data.startswith(codecs.BOM_UTF16_LE):
        return "UTF-16 LE", 2
    if data.startswith(codecs.BOM_UTF16_BE):
        return "UTF-16 BE", 2
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return "ANSI", 0
    return "UTF-8", 0


def detect_eol(text, default="LF"):
    """The most common line ending of a text ("CRLF", "LF" or "CR")."""
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    # On a tie Windows' own line ending wins, then Unix'.
    best = max((crlf, 2, "CRLF"), (lf, 1, "LF"), (cr, 0, "CR"))
    return best[2] if best[0] > 0 else default


def codec(encoding, lang="en"):
    return {"UTF-8": "utf-8", "UTF-8 with BOM": "utf-8", "UTF-16 LE": "utf-16-le",
            "UTF-16 BE": "utf-16-be", "ANSI": ansi_codec(lang)}[encoding]


def decode(data, lang="en"):
    """(text with "\\n" line ends, encoding, eol) of a file's bytes."""
    encoding, skip = detect_encoding(data)
    text = data[skip:].decode(codec(encoding, lang), errors="replace")
    eol = detect_eol(text)
    return text.replace("\r\n", "\n").replace("\r", "\n"), encoding, eol


def encode(text, encoding="UTF-8", eol="LF", lang="en"):
    """The bytes of an editor text saved with an encoding and line ending.
    Characters ANSI cannot hold become "?" as in Windows' Notepad."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", EOLS[eol])
    data = text.encode(codec(encoding, lang), errors="replace")
    bom = {"UTF-8 with BOM": codecs.BOM_UTF8, "UTF-16 LE": codecs.BOM_UTF16_LE,
           "UTF-16 BE": codecs.BOM_UTF16_BE}.get(encoding, b"")
    return bom + data


def load(path, lang="en"):
    """Read a file: (text, encoding, eol). Raises OSError (also for files
    that are too big) and IsADirectoryError."""
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise OSError(f"{path}: file too large")
    return decode(path.read_bytes(), lang)


def save(path, text, encoding="UTF-8", eol="LF", lang="en"):
    """Write atomically (a temporary file renamed over the old one), keeping
    the old file's permissions."""
    path = Path(path)
    data = encode(text, encoding, eol, lang)
    mode = None
    try:
        mode = path.stat().st_mode & 0o7777
    except OSError:
        pass
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def line_column(text, position):
    """1-based (line, column) of a character position in an editor text."""
    position = max(0, min(position, len(text)))
    line = text.count("\n", 0, position) + 1
    column = position - (text.rfind("\n", 0, position) + 1) + 1
    return line, column


def line_start(text, line):
    """Character position of the start of a 1-based line (clamped)."""
    position = 0
    for _ in range(max(0, line - 1)):
        found = text.find("\n", position)
        if found < 0:
            break
        position = found + 1
    return position
