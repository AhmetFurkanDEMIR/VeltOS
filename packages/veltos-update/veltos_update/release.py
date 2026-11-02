"""The newest VeltOS release and the one this PC runs.

A VeltOS release is a GitHub release of the project (built by GitHub
Actions, .github/workflows/release.yml): the ISO for new installations,
and every VeltOS package with a signed package index, which installed
PCs use as their VeltOS package source (data/veltos.sources). So the
newest release's packages are what an update installs; this module only
tells which release that is and what it brings, from GitHub's releases
API (`releases/latest`, no key, 60 requests an hour per address: a PC
asks once a day).

The release text is Markdown with the English notes first and the Turkish
ones after the line `<!-- tr -->` (docs/release-notes/VERSION.md).

/etc/veltos/update.conf may name another address for the release
information (`[Update] release_url = ...`, also file:// for tests).
"""

import configparser
import json
import re
import urllib.request
from pathlib import Path

REPOSITORY = "AhmetFurkanDEMIR/VeltOS"
LATEST_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPOSITORY}/releases"
CONF = Path("/etc/veltos/update.conf")
OS_RELEASE = Path("/etc/os-release")
TR_MARKER = "<!-- tr -->"


def release_url(conf=CONF):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(conf, encoding="utf-8")
    except (OSError, configparser.Error):
        return LATEST_URL
    return parser.get("Update", "release_url", fallback=LATEST_URL).strip() or LATEST_URL


def installed_version(os_release=OS_RELEASE):
    """VERSION_ID of /etc/os-release ("1.1"), which veltos-base sets."""
    try:
        text = Path(os_release).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    match = re.search(r'^VERSION_ID="?([^"\n]*)"?\s*$', text, re.M)
    return match.group(1).strip() if match else ""


def version_key(text):
    """(1, 10, 2) for "v1.10.2" or "1.10.2"; () when it is no version."""
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)", (text or "").strip())
    if not match:
        return ()
    parts = [int(p) for p in match.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()                      # 1.1 == 1.1.0
    return tuple(parts)


def newer(latest, installed):
    """True when release `latest` is newer than the installed version."""
    a, b = version_key(latest), version_key(installed)
    return bool(a) and (not b or a > b)


def notes(body, lang):
    """The release text in the PC's language (English before the marker,
    Turkish after it; English when there is no Turkish part)."""
    body = (body or "").replace("\r\n", "\n")
    english, marker, turkish = body.partition(TR_MARKER)
    text = turkish if (lang == "tr" and marker and turkish.strip()) else english
    # A first heading naming the release repeats what the page shows above
    # the notes ("What's new in VeltOS 1.1"); the ISO's download line
    # (build/scripts/release-notes.py) is for new installations only.
    text = re.sub(r"\A\s*#{1,2} VeltOS [^\n]*\n", "", text.strip() + "\n")
    text = re.sub(r"^\*\*(?:Download|İndirme):\*\* [^\n]*\n?", "", text, flags=re.M)
    return text.strip()


def parse(data):
    """What VeltOS shows of a release from GitHub's JSON."""
    if not isinstance(data, dict) or not data.get("tag_name"):
        raise ValueError("not a release")
    tag = str(data["tag_name"])
    iso = next((a for a in data.get("assets") or [] if str(a.get("name", "")).endswith(".iso")), None)
    return {
        "tag": tag,
        "version": tag[1:] if tag.startswith("v") else tag,
        "name": str(data.get("name") or f"VeltOS {tag}"),
        "body": str(data.get("body") or ""),
        "published": str(data.get("published_at") or ""),
        "url": str(data.get("html_url") or RELEASES_PAGE),
        "iso": {"name": iso.get("name", ""), "size": int(iso.get("size") or 0),
                "url": iso.get("browser_download_url", "")} if iso else {},
    }


def fetch(url=None, timeout=20, opener=urllib.request.urlopen):
    """The newest release (parse()); raises OSError/ValueError when GitHub
    cannot be reached or answers something else."""
    request = urllib.request.Request(url or release_url(), headers={
        "Accept": "application/vnd.github+json", "User-Agent": "VeltOS-Update"})
    with opener(request, timeout=timeout) as response:
        return parse(json.loads(response.read().decode("utf-8")))
