"""VeltOS' package source, used only while it works.

VeltOS' packages are files of the newest GitHub release (a flat APT
repository with a signed index, build/scripts/make-apt-repo.sh). A release
made without them (VeltOS 1.0 has only the ISO) would make every `apt
update` and every PackageKit refresh fail ("does not have a Release
file"): VeltOS Store, VeltOS Graphics Cards and the first start's update
all refresh first. So the source is not a fixed file: this module, run as
root by veltos-update-source.timer, writes
/etc/apt/sources.list.d/veltos.sources while the newest release has an
index signed with VeltOS' key, and removes it while the release has none.
When GitHub cannot be reached it changes nothing.

/etc/veltos/update.conf may name another repository (`[Update]
repository = URL`, the dev VM's tests).
"""

import configparser
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from veltos_update import release

REPOSITORY = f"https://github.com/{release.REPOSITORY}/releases/latest/download/"
SOURCES = Path("/etc/apt/sources.list.d/veltos.sources")
KEYRING = Path("/usr/share/keyrings/veltos-archive-keyring.gpg")
MARK = "# Written by /usr/libexec/veltos/update-source"


def repository(conf=release.CONF):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(conf, encoding="utf-8")
    except (OSError, configparser.Error):
        return REPOSITORY
    url = parser.get("Update", "repository", fallback="").strip() or REPOSITORY
    return url if url.endswith("/") else url + "/"


def text(url, keyring=KEYRING):
    return (f"{MARK} (veltos-update-source.timer)\n"
            "# while the newest VeltOS release carries VeltOS' signed package index;\n"
            "# removed while it does not. VeltOS Update installs from it.\n"
            "Types: deb\n"
            f"URIs: {url}\n"
            "Suites: ./\n"
            f"Signed-By: {Path(keyring).as_posix()}\n")


def probe(url, opener=urllib.request.urlopen, timeout=30):
    """("ok", InRelease bytes), ("missing", None) for a 404, or ("error", why)."""
    request = urllib.request.Request(url + "InRelease", headers={"User-Agent": "VeltOS-Update"})
    try:
        with opener(request, timeout=timeout) as response:
            return "ok", response.read(1 << 20)
    except urllib.error.HTTPError as error:
        return ("missing", None) if error.code == 404 else ("error", f"HTTP {error.code}")
    except (urllib.error.URLError, OSError, ValueError) as error:
        return "error", str(getattr(error, "reason", error))


def signed(data, keyring=KEYRING, run=subprocess.run):
    """True when `data` (an InRelease file) carries a good signature of the key."""
    with tempfile.NamedTemporaryFile(suffix=".InRelease") as handle:
        handle.write(data)
        handle.flush()
        result = run(["gpgv", "--quiet", "--keyring", str(keyring), handle.name],
                     capture_output=True, text=True)
    return result.returncode == 0


def apply(state, url, sources=SOURCES, keyring=KEYRING):
    """Writes or removes the source; returns "enabled", "disabled" or ""."""
    if state == "ok":
        wanted = text(url, keyring)
        try:
            if sources.read_text(encoding="utf-8") == wanted:
                return ""
        except OSError:
            pass
        sources.parent.mkdir(parents=True, exist_ok=True)
        temporary = sources.with_name(sources.name + ".new")
        temporary.write_text(wanted, encoding="utf-8")
        temporary.chmod(0o644)
        temporary.replace(sources)
        return "enabled"
    if state == "missing" and sources.exists():
        sources.unlink()
        return "disabled"
    return ""


def main(conf=release.CONF, sources=SOURCES, keyring=KEYRING, opener=urllib.request.urlopen,
         run=subprocess.run, log=print):
    url = repository(conf)
    state, data = probe(url, opener)
    if state == "ok" and not signed(data, keyring, run):
        log(f"{url}InRelease is not signed with VeltOS' key: the source stays as it was")
        return 1
    if state == "error":
        log(f"{url}: {data}; the source stays as it was")
        return 0
    change = apply(state, url, sources, keyring)
    log({"enabled": f"VeltOS' package source is on ({url})",
         "disabled": f"the newest release has no VeltOS package index: the source is off ({url})",
         "": f"VeltOS' package source: no change ({state})"}[change])
    return 0
